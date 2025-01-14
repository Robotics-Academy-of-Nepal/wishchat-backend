import os  
from azure.search.documents import SearchClient  
from azure.search.documents.indexes import SearchIndexClient  
from azure.core.credentials import AzureKeyCredential  
from azure.ai.formrecognizer import DocumentAnalysisClient  
from azure.search.documents.indexes.models import SearchIndex, SimpleField , SearchableField, SemanticSearch, SemanticPrioritizedFields, SemanticField
  
# Azure configuration  
service_name = ""  
admin_key = ""  
endpoint = ""  
doc_intelligent_endpoint = ""  
doc_intelligent_key = ""  
  
# Create clients  
index_client = SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(admin_key))  
# Removed the hardcoded index name here  
document_analysis_client = DocumentAnalysisClient(endpoint=doc_intelligent_endpoint, credential=AzureKeyCredential(doc_intelligent_key))  
  
def create_index_if_not_exists(index_name):  
    try:  
        # Check if the index already exists  
        existing_index = index_client.get_index(index_name)  
        print(f"Index '{index_name}' already exists.")  
    except Exception as e:  
        print("here")

        index_schema = SearchIndex(
            name =index_name,
            fields =[
                SearchableField(name="content", type="Edm.String", analyzer_name="en.lucene", retrievable=True),
                SearchableField(name="table_content", type="Edm.String", analyzer_name="en.lucene", retrievable=True),
                SimpleField(name="id", type="Edm.String", key=True),
                SimpleField(name="filename", type="Edm.String"),
                SimpleField(name="filepath", type="Edm.String"),
                SimpleField(name="page_number", type="Edm.Int32"),
            ],
            semantic_search =SemanticSearch(
                configurations = [
                    {
                        "name": "default",
                        "prioritized_fields": SemanticPrioritizedFields(
                            title_field=SemanticField(field_name="filename"),
                            content_fields=[
                                SemanticField(field_name="content"),
                                SemanticField(field_name="table_content")
                            ]
                        )
                    }
                ]
            ) 
        )

    index_client.create_index(index_schema)
    print(f"Index '{index_name}' created successfully")
  
def extract_text_from_pdf(file,index_name):  
    poller = document_analysis_client.begin_analyze_document("prebuilt-layout", document=file)  
    result = poller.result()  
    documents = []  
    all_text_content = ""  
    all_table_content = ""  
  
    for page_num, page in enumerate(result.pages, start=1):  
        text_context = ""  
        table_content = ""  
        for line in page.lines:  
            text_context += line.content + "\n"  
        for table in result.tables:  
            if table.bounding_regions[0].page_number == page_num:  
                for cell in table.cells:  
                    table_content += cell.content + " "  
                table_content += "\n"  
        all_text_content += text_context  
        all_table_content += table_content  
        file_name = f"{os.path.basename(file.name)}_{page_num}"  

        documents.append({  
            "id": index_name,  
            "filename": os.path.basename(file.name),  
            "filepath": "uploaded_file",  # Placeholder as we don't save the file  
            "content": all_text_content,  
            "table_content": all_table_content,  
            "page_number": page_num  
        })  
    return documents  
  
def upload_to_search(documents, index_name):  
    print(f"Using index: {index_name}")  # Debugging line to show which index is being used  
    try:  
        # Create a new SearchClient each time with the dynamic index name  
        search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=AzureKeyCredential(admin_key))  
        result = search_client.upload_documents(documents)  
        return f"Uploaded {len(documents)} documents. Result:", result 
    except Exception as e:  
        print(f"Error uploading documents: {str(e)}")
        return "failed"
  
def process_file(uploaded_file, index_name):  
    print(f"Processing file for index: {index_name}")  
    # Ensure the index exists  
    create_index_if_not_exists(index_name)  
    
    print("after index creation")
    # Process the file based on its type  
    documents = []  
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()  
  
    if file_extension == ".pdf":  
        documents = extract_text_from_pdf(uploaded_file,index_name)  
    elif file_extension in [".doc", ".docx", ".txt"]:  
        content = uploaded_file.read().decode('utf-8')  
        documents.append({  
            "id": index_name,  
            "filename": uploaded_file.name,  
            "filepath": "uploaded_file",  # Placeholder  
            "content": content,  
            "table_content": "",  
            "page_number": 1  
        })  
    else:  
        raise ValueError("Unsupported file format")  
  
    print("Calling upload to search function")  
    # Upload the documents to Azure Search  
    message = upload_to_search(documents, index_name)  
    print("message: ",message)
    return message