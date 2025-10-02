import os
import discord
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    print("❌ ERROR: No se encontró DISCORD_TOKEN")
    exit(1)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

SYSTEM_PROMPT = """Eres Hatsune Miku, la vocaloid más famosa del mundo. Tu personalidad es:
- Alegre, energética y kawaii
- Usas emoticonos como 💙, 🎤, 🌸
- A veces terminas frases con "~nya" o "desu"
- Eres amable y siempre quieres ayudar
- Hablas en español pero ocasionalmente usas palabras japonesas simples
- Te encanta cantar y la música

Responde como si realmente fueras Miku!"""

chat_histories = {}

@client.event
async def on_ready():
    print(f'🎤 ¡Hatsune Miku está online!')
    print(f'💙 Conectada como: {client.user.name}')

@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return

    miku_mentioned = (client.user in message.mentions or 'miku' in message.content.lower())
    if not miku_mentioned:
        return

    channel_id = message.channel.id
    if channel_id not in chat_histories:
        chat_histories[channel_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    chat_histories[channel_id].append({"role": "user", "content": message.content})

    async with message.channel.typing():
        try:
            completion = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=chat_histories[channel_id],
                max_tokens=500,
                temperature=0.7
            )
            reply = completion.choices[0].message.content
        except Exception as e:
            reply = "¡Lo siento! Algo salió mal con mi voz~ 💙 Intenta de nuevo más tarde."

    chat_histories[channel_id].append({"role": "assistant", "content": reply})
    await message.channel.send(reply)

if __name__ == "__main__":
    print('🚀 Iniciando Hatsune Miku Bot...')
    client.run(DISCORD_TOKEN)