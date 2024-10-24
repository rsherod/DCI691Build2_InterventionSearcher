#This should fix the problems uploading and using complicated .pdfs use it if the .pdf loading isn't work for you

#IMPORTANT First remove this package from your imports 'from PyPDF2 import PdfReader' no longer needed

# find and replace 'Process uploaded PDF' code block with the following, keep indenting to match
# This goes AFTER 'st.session_state.temperature = temperature' and BEFORE 'clear_button' 
# File upload section
if uploaded_pdf:
    try:
        # Upload file using File API with mime_type specified
        uploaded_file = genai.upload_file(uploaded_pdf, mime_type="application/pdf")
        st.session_state.uploaded_file = uploaded_file
        st.success("File uploaded successfully!")
                  
    except Exception as e:
        st.error(f"Error uploading file: {e}")
        st.session_state.debug.append(f"File upload error: {e}")


#Find 'generate response with error handling' and replace with this keep indentions the same

        # Generate response with error handling
        try:
            if st.session_state.uploaded_file:
                # If there's an uploaded file, include it in the generation
                response = st.session_state.chat_session.send_message([
                    st.session_state.uploaded_file,
                    current_message["content"]
                ])
            else:
                # Otherwise, just use the text prompt
                response = st.session_state.chat_session.send_message(current_message["content"])

            full_response = response.text
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.session_state.debug.append("Assistant response generated")

        except Exception as e:
            st.error(f"An error occurred while generating the response: {e}")
            st.session_state.debug.append(f"Error: {e}")