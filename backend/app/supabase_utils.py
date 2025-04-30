import os
from supabase import create_client, Client
from llama_index.core.memory import ChatMemoryBuffer

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)

def save_memory(run_id: str, memory: ChatMemoryBuffer):
    memory_dict = memory.model_dump()
    supabase.schema("test") \
        .table("chat_memory") \
        .upsert({
            "run_id": run_id,
            "chat_history": memory_dict
        }, on_conflict="run_id").execute()
    print("Memory saved to supabase")

def get_memory(run_id: str):
    response = (
        supabase.schema("test")
        .table("chat_memory")
        .select("*")
        .eq("run_id", run_id)
        .execute()
    )
    if response.data:
        return ChatMemoryBuffer.from_dict(response.data[0]["chat_history"])
    else:
        return None

if __name__ == "__main__":
    
    print(url, key)
    supabase: Client = create_client(url, key)
    response = (
        supabase.schema("test")
        .table("chat_memory")
        .select("*")
        .execute()
    )
    print(response)
