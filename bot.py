import os
import threading
import discord
from discord.ext import commands
from flask import Flask
# ============================================================
# CONFIGURACIÓN
# ============================================================
TOKEN = os.getenv("DISCORD_TOKEN")
PORT = int(os.getenv("PORT", "10000"))
# ID DEL SERVIDOR
GUILD_ID = int(os.getenv("GUILD_ID", "1534290216418938891"))
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
    # CARGAR COGS
    # ========================================================
    async def setup_hook(self):
        print(
            "🔄 Cargando Auto Role...",
            flush=True
        )
        try:
            await self.load_extension(
                "cogs.iconrole",
            )
            print(
                "✅ cogs.autorole cargado correctamente",
                flush=True
            )
        except Exception as e:
            print(
                "❌ ERROR CARGANDO cogs.autorole",
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
        print(
            "====================================",
            flush=True
        )
        # ----------------------------------------------------
        # BUSCAR SERVIDOR
        # ----------------------------------------------------
        guild = self.get_guild(GUILD_ID)
        if guild is None:
            print(
                f"❌ No encontré el servidor {GUILD_ID}",
                flush=True
            )
            print(
                "Verificá que el bot esté dentro del servidor.",
                flush=True
            )
            return
        print(
            f"🏠 Servidor encontrado: {guild.name}",
            flush=True
        )
        # ----------------------------------------------------
        # COPIAR COMANDOS AL SERVIDOR
        # ----------------------------------------------------
        try:
            self.tree.copy_global_to(
                guild=guild
            )
            print(
                "📋 Comandos copiados al servidor.",
                flush=True
            )
        except Exception as e:
            print(
                "❌ Error copiando comandos:",
                flush=True
            )
            print(
                f"{type(e).__name__}: {e}",
                flush=True
            )
            return
        # ----------------------------------------------------
        # SINCRONIZAR
        # ----------------------------------------------------
        try:
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
            "❌ FALTA DISCORD_TOKEN",
            flush=True
        )
    else:
        bot.run(TOKEN)