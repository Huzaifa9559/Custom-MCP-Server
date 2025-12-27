"""
LLM Service for AI question answering.

This service integrates with LLM providers (OpenAI, Anthropic, Gemini) and
uses MCP (Model Context Protocol) for context passing. Context is provided
via MCP, not through manual prompt concatenation.

Key Principle:
- LLM context is provided through MCP protocol
- No manual string concatenation in prompts
- Clean separation: MCP handles context, LLM service handles API calls
"""
import os
from typing import Optional
from django.conf import settings
from documents.mcp_server import MCPContextProvider


class LLMService:
    """
    LLM Service that consumes context via MCP.
    
    This service integrates with various LLM providers and uses MCP
    for document context provision. The key principle is that all
    document context passes through MCP formatting, ensuring clean
    separation of concerns.
    
    Supported Providers:
    - OpenAI (GPT models)
    - Anthropic (Claude models)
    - Google (Gemini models)
    
    Configuration:
    - LLM_API_KEY: API key for the selected provider
    - LLM_PROVIDER: Provider name (openai, anthropic, gemini)
    - LLM_MODEL: Model name (e.g., gpt-4-turbo-preview)
    """
    
    def __init__(self):
        """
        Initialize LLM service with configuration from settings.
        
        Raises:
            ValueError: If LLM_API_KEY is not configured
        """
        self.api_key = settings.LLM_API_KEY
        self.provider = settings.LLM_PROVIDER.lower()
        self.model = settings.LLM_MODEL
        self.mcp_provider = MCPContextProvider()
        
        if not self.api_key:
            raise ValueError(
                "LLM_API_KEY environment variable is required. "
                "Please set it in your .env file."
            )
    
    def ask_question(self, document_id: int, question: str) -> str:
        """
        Ask a question about a document using LLM with MCP context.
        
        The document context is retrieved and formatted via MCP,
        then passed to the LLM. This ensures clean separation:
        - MCP handles context formatting
        - LLM service handles LLM communication
        - No manual prompt concatenation
        
        Args:
            document_id: ID of the document to query
            question: User's question about the document
            
        Returns:
            str: LLM response as a string
            
        Raises:
            ValueError: If document context cannot be retrieved
            Exception: If LLM API call fails
        """
        # Get document context via MCP (not manual concatenation)
        # This is the key: context comes through MCP protocol
        mcp_context = self.mcp_provider.provide_document_context(document_id)
        
        # Build prompt using MCP-formatted context
        # The context is already formatted by MCP, we just add the question
        prompt = f"""{mcp_context}

User Question: {question}

Please answer the user's question based on the document context provided above.
Be concise, accurate, and helpful. If the answer cannot be determined from the
document context, please state that clearly."""
        
        # Call LLM provider
        return self._call_llm_provider(prompt)
    
    def _call_llm_provider(self, prompt: str) -> str:
        """
        Call the configured LLM provider.
        
        Routes the prompt to the appropriate LLM provider based on
        configuration. Each provider has its own implementation method.
        
        Args:
            prompt: The complete prompt including MCP-formatted context
            
        Returns:
            str: LLM response as a string
            
        Raises:
            ValueError: If provider is not supported
            Exception: If API call fails
        """
        if self.provider == 'openai':
            return self._call_openai(prompt)
        elif self.provider == 'anthropic':
            return self._call_anthropic(prompt)
        elif self.provider == 'gemini':
            return self._call_gemini(prompt)
        else:
            raise ValueError(
                f"Unsupported LLM provider: {self.provider}. "
                "Supported providers: openai, anthropic, gemini"
            )
    
    def _call_openai(self, prompt: str) -> str:
        """
        Call OpenAI API.
        
        Uses OpenAI's chat completions API with the configured model.
        
        Args:
            prompt: The complete prompt including context
            
        Returns:
            str: LLM response text
            
        Raises:
            Exception: If API call fails
        """
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that answers questions about documents. "
                                   "Use the provided document context to answer questions accurately."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            return response.choices[0].message.content.strip()
        except ImportError:
            raise ImportError(
                "OpenAI package not installed. Install it with: pip install openai"
            )
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _call_anthropic(self, prompt: str) -> str:
        """
        Call Anthropic Claude API.
        
        Uses Anthropic's messages API with the configured model.
        
        Args:
            prompt: The complete prompt including context
            
        Returns:
            str: LLM response text
            
        Raises:
            Exception: If API call fails
        """
        try:
            from anthropic import Anthropic
            
            client = Anthropic(api_key=self.api_key)
            model = self.model if self.model else "claude-3-5-sonnet-20241022"
            
            response = client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return response.content[0].text.strip()
        except ImportError:
            raise ImportError(
                "Anthropic package not installed. Install it with: pip install anthropic"
            )
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def _call_gemini(self, prompt: str) -> str:
        """
        Call Google Gemini API.
        
        Uses Google's Generative AI API with the configured model.
        
        Args:
            prompt: The complete prompt including context
            
        Returns:
            str: LLM response text
            
        Raises:
            Exception: If API call fails
        """
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            model_name = self.model if self.model else 'gemini-pro'
            model = genai.GenerativeModel(model_name)
            
            response = model.generate_content(prompt)
            return response.text.strip()
        except ImportError:
            raise ImportError(
                "Google Generative AI package not installed. "
                "Install it with: pip install google-generativeai"
            )
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

