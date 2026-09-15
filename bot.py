import os
import json
import threading
from pathlib import Path
import discord
from discord.ext import commands
from flask import Flask
import sys
import discord

print(f"[SYSTEM] Python: {sys.version}")
print(f"[SYSTEM] discord.py: {discord.__version__}")

try:
    import nacl
    print(f"[SYSTEM] PyNaCl: {nacl.__version__}")
except Exception as e:
    print(f"[SYSTEM] PyNaCl ERROR: {e}")
# ============================================================
# CONFIGURACIÓN
# ============================================================
TOKEN = os.getenv("DISCORD_TOKEN")
PORT = int(
    os.getenv(
        "PORT",
        "10000"
    )
)
GUILD_ID = int(
    os.getenv(
        "GUILD_ID",
        "1534290216418938891"
    )
)
PREFIX = "!"
COGS_DIR = Path("cogs")
DATA_DIR = Path("data")
# ============================================================
# CREAR CARPETAS AUTOMÁTICAMENTE
# ============================================================
COGS_DIR.mkdir(
    exist_ok=True
)
DATA_DIR.mkdir(
    exist_ok=True
)
# ============================================================
# SISTEMA DE DATOS
# ============================================================
def get_cog_data_file(cog_name: str):
    """
    Devuelve automáticamente:
    data/nombre_del_cog.json
    """
    return DATA_DIR / f"{cog_name}.json"
def create_cog_data_file(cog_name: str):
    """
    Crea el archivo JSON del Cog si todavía no existe.
    """
    file = get_cog_data_file(
        cog_name
    )
    if not file.exists():
        with open(
            file,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                {},
                f,
                indent=4,
                ensure_ascii=False
            )
        print(
            f"💾 Archivo creado: {file}",
            flush=True
        )
    return file
def load_cog_data(cog_name: str):
    """
    Carga los datos persistentes de un Cog.
    """
    file = create_cog_data_file(
        cog_name
    )
    try:
        with open(
            file,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)
    except Exception as e:
        print(
            f"⚠️ Error leyendo {file}: "
            f"{type(e).__name__}: {e}",
            flush=True
        )
        return {}
def save_cog_data(
    cog_name: str,
    data: dict
):
    """
    Guarda los datos persistentes de un Cog.
    """
    file = create_cog_data_file(
        cog_name
    )
    try:
        with open(
            file,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )
        return True
    except Exception as e:
        print(
            f"❌ Error guardando {file}: "
            f"{type(e).__name__}: {e}",
            flush=True
        )
        return False
# ============================================================
# FLASK
# ============================================================
app = Flask(__name__)
@app.route("/")
def home():
    return "Auto Role Bot online ✅"
@app.route("/health")
def health():
    return "OK", 200
def run_flask():
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False
    )
# ============================================================
# INTENTS
# ============================================================
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True
intents.presences = True
# ============================================================
# BOT
# ============================================================
class AutoRoleBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=PREFIX,
            intents=intents,
            help_command=None
        )
        # Exponer sistema de datos a los Cogs
        self.data_dir = DATA_DIR
        self.load_cog_data = load_cog_data
        self.save_cog_data = save_cog_data
    # ========================================================
    # CARGAR COGS AUTOMÁTICAMENTE
    # ========================================================
    async def setup_hook(self):
        print(
            "🔄 Buscando Cogs...",
            flush=True
        )
        cog_files = sorted(
            COGS_DIR.glob("*.py")
        )
        for file in cog_files:
            # Ignorar __init__.py
            if file.name == "__init__.py":
                continue
            cog_name = file.stem
            extension = (
                f"cogs.{cog_name}"
            )
            # ------------------------------------------------
            # CREAR DATA AUTOMÁTICAMENTE
            # ------------------------------------------------
            create_cog_data_file(
                cog_name
            )
            # ------------------------------------------------
            # CARGAR COG
            # ------------------------------------------------
            try:
                await self.load_extension(
                    extension
                )
                print(
                    f"✅ Cog cargado: {extension}",
                    flush=True
                )
            except Exception as e:
                print(
                    f"❌ Error cargando {extension}",
                    flush=True
                )
                print(
                    f"   {type(e).__name__}: {e}",
                    flush=True
                )
        # ====================================================
        # MOSTRAR COMANDOS
        # ====================================================
        commands_loaded = (
            self.tree.get_commands()
        )
        print(
            "",
            flush=True
        )
        print(
            "📋 Comandos encontrados:",
            flush=True
        )
        if not commands_loaded:
            print(
                "   ⚠️ No hay comandos.",
                flush=True
            )
        else:
            for command in commands_loaded:
                print(
                    f"   /{command.name}",
                    flush=True
                )
        # ====================================================
        # SINCRONIZAR AL SERVIDOR
        # ====================================================
        guild = discord.Object(
            id=GUILD_ID
        )
        try:
            self.tree.copy_global_to(
                guild=guild
            )
            synced = await self.tree.sync(
                guild=guild
            )
            print(
                "",
                flush=True
            )
            print(
                f"✅ {len(synced)} comandos sincronizados.",
                flush=True
            )
            for command in synced:
                print(
                    f"   /{command.name}",
                    flush=True
                )
        except Exception as e:
            print(
                "❌ ERROR SINCRONIZANDO COMANDOS",
                flush=True
            )
            print(
                f"{type(e).__name__}: {e}",
                flush=True
            )
    # ========================================================
    # READY
    # ========================================================
    async def on_ready(self):
        print(
            "",
            flush=True
        )
        print(
            "====================================",
            flush=True
        )
        print(
            f"🤖 Bot: {self.user}",
            flush=True
        )
        print(
            f"🆔 ID: {self.user.id}",
            flush=True
        )
        print(
            f"🌐 Servidores: {len(self.guilds)}",
            flush=True
        )
        guild = self.get_guild(
            GUILD_ID
        )
        if guild:
            print(
                f"🏠 Servidor: {guild.name}",
                flush=True
            )
        else:
            print(
                f"⚠️ No encontré el servidor {GUILD_ID}",
                flush=True
            )
        print(
            "====================================",
            flush=True
        )
# ============================================================
# CREAR BOT
# ============================================================
bot = AutoRoleBot()
# ============================================================
# INICIAR
# ============================================================
if __name__ == "__main__":
    print(
        "🚀 Iniciando Auto Role Bot...",
        flush=True
    )
    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )
    flask_thread.start()
    if not TOKEN:
        print(
            "❌ ERROR: Falta DISCORD_TOKEN.",
            flush=True
        )
    else:
        bot.run(
            TOKEN
        )