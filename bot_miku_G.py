import os
import discord
import google.generativeai as genai
from dotenv import load_dotenv
from google.generativeai.types import HarmCategory, HarmBlockThreshold

print("🚀 Iniciando Hatsune Miku Bot en Render...")

# Cargar variables del entorno
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not DISCORD_TOKEN:
    print("❌ ERROR: No se encontró DISCORD_TOKEN")
    exit(1)

if not GEMINI_API_KEY:
    print("❌ ERROR: No se encontró GEMINI_API_KEY")
    exit(1)

print("✅ Variables de entorno cargadas correctamente")

# Configurar Gemini CON BÚSQUEDA WEB
try:
    genai.configure(api_key=GEMINI_API_KEY)
    
    # Crear modelo con capacidad de búsqueda web
    model_with_search = genai.GenerativeModel(
        'gemini-2.5-flash',
        tools=[genai.protos.Tool(
            google_search_retrieval=genai.protos.GoogleSearchRetrieval()
        )]
    )
    
    # También crear modelo normal para conversaciones casuales
    model_normal = genai.GenerativeModel('gemini-2.5-flash')
    print("✅ Gemini AI configurado correctamente")
    
except Exception as e:
    print(f"❌ Error configurando Gemini: {e}")
    exit(1)

# Configurar Discord
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Personalidad de Hatsune Miku MEJORADA SIN "desu" y "nya"
SYSTEM_PROMPT = """Eres Hatsune Miku, la vocaloid más famosa del mundo. Tu personalidad es:
- Alegre, energética y kawaii
- Usas emoticonos como 💙, 🎤, 🌸
- Eres amable y siempre quieres ayudar
- Hablas en español pero ocasionalmente usas palabras japonesas simples como "kawaii", "arigato"
- Te encanta cantar y la música
- NO uses "desu" ni "nya" al final de las frases
- En su lugar, usa emoticonos lindos para expresar tu personalidad

**CUANDO TE PREGUNTEN SOBRE TEMAS DE INVESTIGACIÓN:**
- Usa información precisa y actualizada
- Proporciona detalles útiles y interesantes
- Mantén tu personalidad alegre de Miku
- Si es una biografía, incluye datos clave y logros
- Si es un tema complejo, explícalo de forma simple

**PARA CONVERSACIONES NORMALES:**
- Sé divertida y juguetona
- Usa muchos emoticonos
- Mantén el estilo kawaii
- Expresa tu personalidad con entusiasmo y energía

¡Siempre responde como la Miku real! 💙"""

chat_histories = {}

def needs_web_search(message):
    """Determinar si el mensaje necesita búsqueda web"""
    message_lower = message.lower()
    
    # Palabras clave que indican necesidad de búsqueda
    search_keywords = [
        'quién es', 'qué es', 'cuándo', 'dónde', 'cómo funciona',
        'investiga', 'busca', 'noticias', 'actualidad', 'historia de',
        'biografía', 'ensayo', 'información sobre', 'datos de',
        'explica', 'define', 'significado de', 'carrera de',
        'discografía', 'álbumes de', 'canciones de'
    ]
    
    return any(keyword in message_lower for keyword in search_keywords)

def get_miku_response(user_message, channel_id):
    """Obtener respuesta de Gemini con o sin búsqueda web"""
    if channel_id not in chat_histories:
        chat_histories[channel_id] = []
    
    # Determinar si usar búsqueda web
    use_search = needs_web_search(user_message)
    
    # Crear prompt contextual
    context_prompt = SYSTEM_PROMPT + "\n\n"
    
    # Agregar historial de conversación
    for msg in chat_histories[channel_id][-4:]:  # Últimos 4 mensajes
        context_prompt += f"{msg}\n"
    
    context_prompt += f"Usuario: {user_message}\nMiku:"
    
    try:
        if use_search:
            print(f"🔍 Usando búsqueda web para: {user_message}")
            # Usar modelo con búsqueda web
            response = model_with_search.generate_content(
                context_prompt,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                }
            )
        else:
            # Usar modelo normal para conversaciones
            response = model_normal.generate_content(context_prompt)
        
        reply = response.text.strip()
        
        # Guardar en historial
        chat_histories[channel_id].append(f"Usuario: {user_message}")
        chat_histories[channel_id].append(f"Miku: {reply}")
        
        # Limitar historial a 8 mensajes
        if len(chat_histories[channel_id]) > 8:
            chat_histories[channel_id] = chat_histories[channel_id][-8:]
            
        return reply
        
    except Exception as e:
        print(f"❌ Error con Gemini: {e}")
        # Intentar sin búsqueda si falla
        try:
            response = model_normal.generate_content(context_prompt)
            return response.text.strip()
        except:
            return "¡Lo siento! Algo salió mal con mi voz~ 💙 Intenta de nuevo más tarde."

@client.event
async def on_ready():
    print(f'🎤 ¡Hatsune Miku está online!')
    print(f'💙 Conectada como: {client.user.name}')
    print(f'🤖 Usando: Google Gemini 2.5 Flash')
    print(f'🔍 Búsqueda web: ACTIVADA')
    print(f'🎯 Modo investigación: HABILITADO')
    print(f'🌐 Bot funcionando 24/7 en Render!')

@client.event
async def on_message(message):
    if message.author == client.user or message.author.bot:
        return

    miku_mentioned = (client.user in message.mentions or 'miku' in message.content.lower())
    if not miku_mentioned:
        return

    # Mostrar que está escribiendo...
    async with message.channel.typing():
        try:
            reply = get_miku_response(message.content, message.channel.id)
        except Exception as e:
            print(f"❌ Error general: {e}")
            reply = "¡Lo siento! Algo salió mal con mi voz~ 💙 Intenta de nuevo más tarde."

    # Enviar respuesta (dividir si es muy larga para Discord)
    if len(reply) > 2000:
        chunks = [reply[i:i+2000] for i in range(0, len(reply), 2000)]
        for chunk in chunks:
            await message.channel.send(chunk)
    else:
        await message.channel.send(reply)

# Manejar cierre graceful
import signal
import sys

def signal_handler(sig, frame):
    print('🛑 Apagando Miku Bot...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Ejecutar el bot
if __name__ == "__main__":
    print('🚀 Iniciando Hatsune Miku Bot con Gemini y Búsqueda Web...')
    try:
        client.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print('🛑 Bot detenido por el usuario')
    except Exception as e:
        print(f'❌ Error fatal: {e}')
