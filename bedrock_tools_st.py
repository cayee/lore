# Import libraries
import streamlit as st
from bedrock_tools import AWSWellArchTool, CodeGenerationTool

well_arch_tool = AWSWellArchTool()
code_gen_tool = CodeGenerationTool()


def app() -> None:
    """
    Purpose:
        Controls the app flow
    Args:
        N/A
    Returns:
        N/A
    """

    # Choose tool
    current_tool = st.selectbox(
        "Choose Tool:", ["Loremaster"]
    )

    query = st.text_input("Query:")

    if st.button("Submit Query"):
        with st.spinner("Generating..."):
            if current_tool == "Loremaster":
                answer = well_arch_tool(query)

            if type(answer) == dict:
                st.markdown(answer["ans"])
                docs = answer["docs"].split("\n")

                with st.expander("Resources"):
                    for doc in docs:
                        st.write(doc)
            else:
                st.markdown(answer)


def main() -> None:
    """
    Purpose:
        Controls the flow of the streamlit app
    Args:
        N/A
    Returns:
        N/A
    """

    # Start the streamlit app
    st.title("League of Legends Loremaster")

    app()


if __name__ == "__main__":
    main()
