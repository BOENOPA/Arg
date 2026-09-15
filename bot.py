import os
import sys
import json
import asyncio
import threading
from pathlib import Path
import discord
from discord.ext import commands
from flask import Flask
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
# ============================================================
# RUTAS
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
COGS_DIR = BASE_DIR / "cogs"
DATA_DIR = BASE_DIR / "data"
COGS_DIR.mkdir(
    parents=True,
    exist_ok=True
)
DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)
# ============================================================
# INFORMACIÓN DEL SISTEMA
# ============================================================
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("[SYSTEM] Iniciando bot...")
print(f"[SYSTEM] Python: {sys.version}")
print(f"[SYSTEM] discord.py: {discord.__version__}")
try:
    import nacl
    print(
        f"[SYSTEM] PyNaCl: "
        f"{nacl.__version__}"
    )
except Exception as e:
    print(
        f"[SYSTEM] PyNaCl ERROR: {e}"
    )
print(
    f"[SYSTEM] PORT: {PORT}"
)
print(
    f"[SYSTEM] GUILD_ID: {GUILD_ID}"
)
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
# ============================================================
# INTENTS
# ============================================================
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.presences = True
intents.voice_states = True
intents.message_content = True
# ============================================================
# BOT
# ============================================================
class MiBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=PREFIX,
            intents=intents,
            help_command=None
        )
    # ========================================================
    # SISTEMA DE DATOS
    # ========================================================
    def get_cog_data_file(
        self,
        cog_name: str
    ) -> Path:
        return DATA_DIR / f"{cog_name}.json"
    def create_cog_data_file(
        self,
        cog_name: str,
        default_data=None
    ):
        file_path = self.get_cog_data_file(
            cog_name
        )
        if file_path.exists():
            return
        if default_data is None:
            default_data = {}
        try:
            with file_path.open(
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    default_data,
                    f,
                    ensure_ascii=False,
                    indent=4
                )
            print(
                f"[DATA] ✅ Creado: "
                f"{file_path}"
            )
        except Exception as e:
            print(
                f"[DATA] ❌ Error creando "
                f"{file_path}: {e}"
            )
    def load_cog_data(
        self,
        cog_name: str,
        default_data=None
    ):
        file_path = self.get_cog_data_file(
            cog_name
        )
        if not file_path.exists():
            if default_data is None:
                default_data = {}
            self.create_cog_data_file(
                cog_name,
                default_data
            )
            return default_data
        try:
            with file_path.open(
                "r",
                encoding="utf-8"
            ) as f:
                return json.load(f)
        except (
            json.JSONDecodeError,
            OSError
        ) as e:
            print(
                f"[DATA] ❌ Error leyendo "
                f"{file_path}: {e}"
            )
            if default_data is None:
                default_data = {}
            return default_data
    def save_cog_data(
        self,
        cog_name: str,
        data
    ):
        file_path = self.get_cog_data_file(
            cog_name
        )
        try:
            with file_path.open(
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    data,
                    f,
                    ensure_ascii=False,
                    indent=4
                )
        except Exception as e:
            print(
                f"[DATA] ❌ Error guardando "
                f"{file_path}: {e}"
            )
    # ========================================================
    # CARGAR COGS
    # ========================================================
    async def setup_hook(self):
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("[COGS] 🔄 Cargando extensiones...")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        if not COGS_DIR.exists():
            print(
                "[COGS] ❌ La carpeta cogs no existe."
            )
            return
        cog_files = sorted(
            COGS_DIR.glob("*.py")
        )
        if not cog_files:
            print(
                "[COGS] ⚠️ No hay archivos .py en cogs."
            )
        for file in cog_files:
            if file.name.startswith("_"):
                continue
            extension = (
                f"cogs.{file.stem}"
            )
            try:
                await self.load_extension(
                    extension
                )
                print(
                    f"[COGS] ✅ Cargado: "
                    f"{extension}"
                )
            except Exception as e:
                print(
                    f"[COGS] ❌ Error cargando: "
                    f"{extension}"
                )
                print(
                    f"[COGS] {type(e).__name__}: {e}"
                )
        # ====================================================
        # SINCRONIZACIÓN DE SLASH COMMANDS
        # ====================================================
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("[SLASH] 🔄 Sincronizando comandos...")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        guild_object = discord.Object(
            id=GUILD_ID
        )
        try:
            # ------------------------------------------------
            # COPIAR LOS COMANDOS GLOBALES AL SERVIDOR
            # ------------------------------------------------
            self.tree.copy_global_to(
                guild=guild_object
            )
            # ------------------------------------------------
            # SINCRONIZAR CON DISCORD
            # ------------------------------------------------
            synced = await self.tree.sync(
                guild=guild_object
            )
            print(
                f"[SLASH] ✅ Comandos sincronizados: "
                f"{len(synced)}"
            )
            # ------------------------------------------------
            # MOSTRAR COMANDOS EN CONSOLA
            # ------------------------------------------------
            if synced:
                print(
                    "[SLASH] 📋 Comandos:"
                )
                for command in synced:
                    print(
                        f"[SLASH]    /{command.name}"
                    )
            else:
                print(
                    "[SLASH] ⚠️ Discord recibió 0 comandos."
                )
                print(
                    "[SLASH] ⚠️ Revisá que tus cogs tengan "
                    "@app_commands.command."
                )
        except Exception as e:
            print(
                "[SLASH] ❌ Error sincronizando comandos:"
            )
            print(
                f"[SLASH] {type(e).__name__}: {e}"
            )
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    # ========================================================
    # READY
    # ========================================================
    async def on_ready(self):
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(
            "[DISCORD] ✅ BOT CONECTADO"
        )
        print(
            f"[DISCORD] Usuario: "
            f"{self.user}"
        )
        print(
            f"[DISCORD] ID: "
            f"{self.user.id}"
        )
        print(
            f"[DISCORD] Servidores: "
            f"{len(self.guilds)}"
        )
        print(
            f"[DISCORD] discord.py: "
            f"{discord.__version__}"
        )
        try:
            import nacl
            print(
                f"[DISCORD] PyNaCl: "
                f"{nacl.__version__}"
            )
        except Exception as e:
            print(
                f"[DISCORD] PyNaCl ERROR: {e}"
            )
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    # ========================================================
    # ERRORES DE COMANDOS
    # ========================================================
    async def on_command_error(
        self,
        ctx,
        error
    ):
        if isinstance(
            error,
            commands.CommandNotFound
        ):
            return
        print(
            f"[COMMAND ERROR] "
            f"{type(error).__name__}: {error}"
        )
# ============================================================
# FLASK
# ============================================================
app = Flask(__name__)
@app.route("/")
def home():
    return {
        "status": "online",
        "bot": "Discord Bot",
        "discord": (
            str(bot.user)
            if bot.user
            else "connecting"
        )
    }
@app.route("/health")
def health():
    return {
        "status": "ok",
        "discord_connected": bot.is_ready()
    }
# ============================================================
# FLASK SERVER
# ============================================================
def run_flask():
    print(
        f"[FLASK] 🌐 Servidor iniciado "
        f"en puerto {PORT}"
    )
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False,
        use_reloader=False
    )
# ============================================================
# BOT
# ============================================================
bot = MiBot()
# ============================================================
# MAIN
# ============================================================
async def main():
    if not TOKEN:
        print(
            "[FATAL] ❌ Falta DISCORD_TOKEN."
        )
        return
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("[START] 🚀 Iniciando Discord...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    await bot.start(TOKEN)
# ============================================================
# START BOT
# ============================================================
def start_bot():
    try:
        asyncio.run(
            main()
        )
    except KeyboardInterrupt:
        print(
            "[SYSTEM] Bot detenido."
        )
    except Exception as e:
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(
            "[FATAL] ❌ Error fatal:"
        )
        print(
            f"[FATAL] {type(e).__name__}: {e}"
        )
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        raise
# ============================================================
# EJECUCIÓN
# ============================================================
if __name__ == "__main__":
    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )
    flask_thread.start()
    start_bot()