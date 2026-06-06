import os

from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq


load_dotenv("env.env")


class LLMRouter:

    def __init__(self):
        self.use_fallback = False

    def get_primary_llm(self):

        if not self.use_fallback:

            try:

                llm = ChatGoogleGenerativeAI(
                    model="gemini-3.1-flash-lite",
                    google_api_key=os.getenv("GOOGLE_API_KEY"),
                    temperature=0.2,
                )

                llm.invoke("ping")

                return llm

            except Exception as e:

                print(f"Gemini unavailable: {e}")
                print("Switching to Groq fallback...")

                self.use_fallback = True

        return self.get_fast_llm()

    def get_fast_llm(self):

        return ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.2,
        )


router = LLMRouter()


def get_primary_llm():
    return router.get_primary_llm()


def get_fast_llm():
    return router.get_fast_llm()