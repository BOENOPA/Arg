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

        # Cargar cog
        try:
            await self.load_extension("cogs.autorole")
            print("✅ Cog autorole cargado")
        except Exception as e:
            print(f"❌ Error cargando autorole: {e}")

        # Sincronizar slash commands
        try:
            synced = await self.tree.sync()
            print(f"✅ {len(synced)} comandos slash sincronizados")
        except Exception as e:
            print(f"❌ Error sincronizando comandos: {e}")

    async def on_ready(self):
        print("====================================")
        print(f"🤖 Bot: {self.user}")
        print(f"🆔 ID: {self.user.id}")
        print(f"🌐 Servidores: {len(self.guilds)}")
        print("====================================")


bot = AutoRoleBot()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    # Flask para Render
    flask_thread = threading.Thread(
        target=run_flask,
        daemon=True
    )

    flask_thread.start()

    if not TOKEN:
        print("❌ Falta DISCORD_TOKEN en las variables de entorno.")
    else:
        bot.run(TOKEN)