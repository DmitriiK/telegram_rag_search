# streamlit run ui.py
import streamlit as st

from src.rag_integration import RaguDuDu


def main():
    rg = RaguDuDu()
    st.title("RAG Function Invocation")

    user_input = st.text_input("Enter your input:")

    if st.button("Ask"):
        with st.spinner('Processing your request'):
            ret = rg.rag_by_dense_vector_search(question=user_input)
            st.success("Completed!")
            st.write(ret)


if __name__ == "__main__":
    main()