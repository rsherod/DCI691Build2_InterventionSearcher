#Step 1: Update requirements.txt
#Add this line to your requirements.txt file:#Add Perplexity Search
requests

#Step 2: Add Import
#Find the imports section at the top of your code and add:
import requests


#Step 3: Add Perplexity API Configuration
#After the line that configures the Gemini API:

# Find this line:
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Add this line right after:
PERPLEXITY_API_KEY = st.secrets["P_API_KEY"]

#Step 4: Add Search Function
#Add this function after your session state initialization code (after all the if "something" not in st.session_state blocks) and before the user input handling:
def search_perplexity(query):
    """Execute a search query using Perplexity API"""
    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "accept": "application/json",
                "content-type": "application/json",
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}"
            },
            json={
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [{"role": "user", "content": f"Search the web for: {query}"}]
            }
        )
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"Perplexity API Error: {e}")
        return None

#Step 5: Replace Response Generation Code
#Find the code block that handles generating responses (it starts with if user_input:). Replace everything from there until the st.rerun() with this updated version:
if user_input:
    current_message = {"role": "user", "content": user_input}
    st.session_state.messages.append(current_message)

    with st.chat_message("user"):
        st.markdown(current_message["content"])

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        # Initialize chat session if needed
        if st.session_state.chat_session is None:
            generation_config = {
                "temperature": st.session_state.temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
            model = genai.GenerativeModel(
                model_name=st.session_state.model_name,
                generation_config=generation_config,
            )
            
            initial_messages = [
                {"role": "user", "parts": [f"System: {system_prompt}"]},
                {"role": "model", "parts": ["Understood. I will follow these instructions."]},
            ]
            
            if st.session_state.pdf_content:
                initial_messages.extend([
                    {"role": "user", "parts": [f"PDF content for reference:\n\n{st.session_state.pdf_content}"]},
                    {"role": "model", "parts": ["Acknowledged PDF content."]}
                ])
            
            st.session_state.chat_session = model.start_chat(history=initial_messages)

        try:
            is_search = user_input.lower().startswith(("search", "search the web", "find", "lookup"))
            
            if is_search:
                # Extract search query
                search_query = ' '.join(user_input.split()[2:] if user_input.lower().startswith("search the web") else user_input.split()[1:])
                
                if not search_query:
                    message_placeholder.warning("Please provide a search query.")
                    st.session_state.messages.pop()  # Remove the empty query from history
                    st.rerun()
                
                # Execute search
                message_placeholder.info("🔍 Searching the web...")
                search_results = search_perplexity(search_query)
                
                if search_results:
                    # Process results with Gemini
                    prompt = (
                        f"Here are web search results for: '{search_query}'\n\n"
                        f"{search_results}\n\n"
                        "Please provide a clear, accurate summary of these results in a well-formatted response. "
                        "Include relevant links when available. Verify accuracy before responding."
                    )
                    
                    response = st.session_state.chat_session.send_message(prompt)
                    message_placeholder.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                    st.session_state.debug.append("Search results processed successfully")
            else:
                # Handle regular chat
                response = st.session_state.chat_session.send_message(user_input)
                message_placeholder.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                st.session_state.debug.append("Regular chat response generated")
                
        except Exception as e:
            st.error(f"Error generating response: {e}")
            st.session_state.debug.append(f"Error: {e}")
            st.session_state.messages.pop()  # Remove failed message from history
    
    st.rerun()

#Step 6: Update Streamlit Secrets
#Add your Perplexity API to secrets
P_API_KEY = "your-perplexity-api-key-here"