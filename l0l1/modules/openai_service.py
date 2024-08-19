# app/openai_service.py
import openai
from flask import current_app

class OpenAIService:
    @staticmethod
    def explain_schema(schema_content):
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=f"Explain the following SQL schema:\n\n{schema_content}",
            max_tokens=500
        )
        return response.choices[0].text.strip()

    @staticmethod
    def explain_query(query_content):
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=f"Explain the following SQL query:\n\n{query_content}",
            max_tokens=500
        )
        return response.choices[0].text.strip()

    @staticmethod
    def generate_embedding(text):
        response = openai.Embedding.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response['data'][0]['embedding']

    @staticmethod
    def complete_query(partial_query, suggested_tables):
        tables_str = ", ".join(suggested_tables)
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=f"Complete the following SQL query. Available tables: {tables_str}\n\nQuery: {partial_query}",
            max_tokens=100
        )
        return response.choices[0].text.strip()

    @staticmethod
    def correct_query(query_content):
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=f"Correct any errors in the following SQL query:\n\n{query_content}",
            max_tokens=200
        )
        return response.choices[0].text.strip()