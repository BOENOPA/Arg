import os
import threading
import importlib
from pathlib import Path
import discord
from discord.ext import commands
from flask import Flask
# ============================================================
# CONFIGURACIÓN
# ============================================================
TOKEN = os.getenv("DISCORD_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
GUILD_ID = int(
    os.getenv(
        "GUILD_ID",
        "1534290216418938891"
    )
)
PREFIX = "!"
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
    # ========================================================
    # CARGAR TODOS LOS COGS AUTOMÁTICAMENTE
    # ========================================================
    async def setup_hook(self):
        print(
            "🔄 Buscando Cogs...",
            flush=True
        )
        cogs_path = Path("cogs")
        # ----------------------------------------------------
        # CREAR CARPETA SI NO EXISTE
        # ----------------------------------------------------
        cogs_path.mkdir(
            exist_ok=True
        )
        # ----------------------------------------------------
        # BUSCAR ARCHIVOS .PY
        # ----------------------------------------------------
        cog_files = sorted(
            cogs_path.glob("*.py")
        )
        if not cog_files:
            print(
                "⚠️ No se encontraron Cogs.",
                flush=True
            )
        # ----------------------------------------------------
        # CARGAR CADA COG
        # ----------------------------------------------------
        for file in cog_files:
            # Ignorar __init__.py
            if file.name == "__init__.py":
                continue
            extension = (
                f"cogs.{file.stem}"
            )
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
        commands_loaded = self.tree.get_commands()
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
                "   ⚠️ No hay comandos slash.",
                flush=True
            )
        else:
            for command in commands_loaded:
                print(
                    f"   /{command.name}",
                    flush=True
                )
        # ====================================================
        # SINCRONIZAR DIRECTAMENTE AL SERVIDOR
        # ====================================================
        guild = discord.Object(
            id=GUILD_ID
        )
        try:
            # Copiar comandos globales al servidor
            self.tree.copy_global_to(
                guild=guild
            )
            print(
                "",
                flush=True
            )
            print(
                "🔄 Sincronizando comandos...",
                flush=True
            )
            synced = await self.tree.sync(
                guild=guild
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
    # --------------------------------------------------------
    # FLASK
    # --------------------------------------------------------
    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )
    flask_thread.start()
    # --------------------------------------------------------
    # TOKEN
    # --------------------------------------------------------
    if not TOKEN:
        print(
            "❌ ERROR: Falta DISCORD_TOKEN.",
            flush=True
        )
    else:
        bot.run(
            TOKEN
        )