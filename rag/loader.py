import os


def load_pdfs(data_folder: str) -> list:
    """
    Finds and loads every PDF inside data_folder.
    Returns a combined list of LangChain Document objects (one per page).
    """
    from langchain_community.document_loaders import PyPDFLoader

    if not os.path.isdir(data_folder):
        raise FileNotFoundError(
            f"'{data_folder}' folder not found. Create it and add PDFs."
        )

    pdf_files = [f for f in os.listdir(data_folder) if f.lower().endswith(".pdf")]

    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found inside '{data_folder}/'.")

    all_documents = []
    for filename in pdf_files:
        path = os.path.join(data_folder, filename)
        print(f"Loading {filename}...")
        loader = PyPDFLoader(path)
        all_documents.extend(loader.load())

    return all_documents