import os
import asyncio
import threading
import discord

from discord.ext import commands
from flask import Flask

# ============================================================
# CONFIGURACIÓN
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

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

    async def setup_hook(self):

        print("🔄 Iniciando carga de comandos...")

        # ----------------------------------------------------
        # CARGAR AUTOROLE
        # ----------------------------------------------------

        try:
            await self.load_extension("cogs.autorole")
            print("✅ Cog autorole cargado correctamente")

        except Exception as e:
            print("❌ ERROR CARGANDO COG AUTOROLE")
            print(f"{type(e).__name__}: {e}")

        # ----------------------------------------------------
        # MOSTRAR COMANDOS
        # ----------------------------------------------------

        print("📋 Comandos encontrados:")

        for command in self.tree.get_commands():
            print(f"   /{command.name}")

    async def on_ready(self):

        print("====================================")
        print(f"🤖 Bot: {self.user}")
        print(f"🆔 ID: {self.user.id}")
        print(f"🌐 Servidores: {len(self.guilds)}")
        print("====================================")

        # ----------------------------------------------------
        # SINCRONIZAR SLASH COMMANDS
        # ----------------------------------------------------

        try:

            synced = await self.tree.sync()

            print(
                f"✅ {len(synced)} comandos slash sincronizados"
            )

            for command in synced:
                print(f"   /{command.name}")

        except Exception as e:

            print("❌ ERROR SINCRONIZANDO SLASH COMMANDS")
            print(f"{type(e).__name__}: {e}")


# ============================================================
# CREAR BOT
# ============================================================

bot = AutoRoleBot()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    print("🚀 Iniciando Auto Role Bot...")

    # Flask para Render
    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )

    flask_thread.start()

    if not TOKEN:

        print(
            "❌ ERROR: Falta DISCORD_TOKEN "
            "en las variables de entorno."
        )

    else:

        bot.run(TOKEN)