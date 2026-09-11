import discord
from discord import app_commands
from discord.ext import commands
class Presencia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    # ============================================================
    # COMPROBAR PERMISOS
    # ============================================================
    async def check_admin(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message(
                "❌ Este comando solamente puede utilizarse dentro de un servidor.",
                ephemeral=True
            )
            return False
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "❌ No pude verificar tus permisos.",
                ephemeral=True
            )
            return False
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "❌ Necesitás el permiso **Gestionar servidor**.",
                ephemeral=True
            )
            return False
        return True
    # ============================================================
    # /VCENTRAR
    # ============================================================
    @app_commands.command(
        name="vcentrar",
        description="Hace que el bot entre a un canal de voz."
    )
    @app_commands.describe(
        canal="Canal de voz al que entrará el bot."
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def vcentrar(
        self,
        interaction: discord.Interaction,
        canal: discord.VoiceChannel
    ):
        if not await self.check_admin(interaction):
            return
        try:
            # Si ya está conectado a otro canal
            if interaction.guild.voice_client:
                await interaction.guild.voice_client.move_to(canal)
            else:
                await canal.connect()
            await interaction.response.send_message(
                f"🔊 Me conecté a {canal.mention}.",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ No tengo permisos para conectarme a ese canal.",
                ephemeral=True
            )
        except Exception as e:
            print(f"[PRESENCIA] Error al entrar al VC: {e}")
            await interaction.response.send_message(
                "❌ No pude conectarme al canal de voz.",
                ephemeral=True
            )
    # ============================================================
    # /VCSALIR
    # ============================================================
    @app_commands.command(
        name="vcsalir",
        description="Hace que el bot salga del canal de voz."
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def vcsalir(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_admin(interaction):
            return
        voice_client = interaction.guild.voice_client
        if not voice_client:
            await interaction.response.send_message(
                "❌ No estoy conectado a ningún canal de voz.",
                ephemeral=True
            )
            return
        try:
            await voice_client.disconnect()
            await interaction.response.send_message(
                "👋 Salí del canal de voz.",
                ephemeral=True
            )
        except Exception as e:
            print(f"[PRESENCIA] Error al salir del VC: {e}")
            await interaction.response.send_message(
                "❌ No pude salir del canal de voz.",
                ephemeral=True
            )
    # ============================================================
    # /ESTADO
    # ============================================================
    @app_commands.command(
        name="estado",
        description="Modifica el estado y la actividad del bot."
    )
    @app_commands.describe(
        tipo="Tipo de actividad.",
        texto="Texto que mostrará el bot.",
        estado="Estado de Discord del bot."
    )
    @app_commands.choices(
        tipo=[
            app_commands.Choice(
                name="🎮 Jugando",
                value="playing"
            ),
            app_commands.Choice(
                name="👀 Viendo",
                value="watching"
            ),
            app_commands.Choice(
                name="🎧 Escuchando",
                value="listening"
            ),
            app_commands.Choice(
                name="🏆 Compitiendo",
                value="competing"
            ),
            app_commands.Choice(
                name="❌ Sin actividad",
                value="none"
            )
        ],
        estado=[
            app_commands.Choice(
                name="🟢 Online",
                value="online"
            ),
            app_commands.Choice(
                name="🌙 Ausente",
                value="idle"
            ),
            app_commands.Choice(
                name="⛔ No molestar",
                value="dnd"
            ),
            app_commands.Choice(
                name="⚫ Invisible",
                value="invisible"
            )
        ]
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def estado(
        self,
        interaction: discord.Interaction,
        tipo: app_commands.Choice[str],
        texto: str,
        estado: app_commands.Choice[str]
    ):
        if not await self.check_admin(interaction):
            return
        # ========================================================
        # ESTADO
        # ========================================================
        status_map = {
            "online": discord.Status.online,
            "idle": discord.Status.idle,
            "dnd": discord.Status.dnd,
            "invisible": discord.Status.invisible
        }
        new_status = status_map[estado.value]
        # ========================================================
        # ACTIVIDAD
        # ========================================================
        activity = None
        if tipo.value == "playing":
            activity = discord.Game(
                name=texto
            )
        elif tipo.value == "watching":
            activity = discord.Activity(
                type=discord.ActivityType.watching,
                name=texto
            )
        elif tipo.value == "listening":
            activity = discord.Activity(
                type=discord.ActivityType.listening,
                name=texto
            )
        elif tipo.value == "competing":
            activity = discord.Activity(
                type=discord.ActivityType.competing,
                name=texto
            )
        elif tipo.value == "none":
            activity = None
        try:
            await self.bot.change_presence(
                status=new_status,
                activity=activity
            )
            if tipo.value == "none":
                actividad_texto = "Sin actividad"
            else:
                actividad_texto = (
                    f"{tipo.name}: **{texto}**"
                )
            await interaction.response.send_message(
                "💜 **Presencia actualizada**\n\n"
                f"**Estado:** {estado.name}\n"
                f"**Actividad:** {actividad_texto}",
                ephemeral=True
            )
        except Exception as e:
            print(
                f"[PRESENCIA] Error cambiando presencia: {e}"
            )
            await interaction.response.send_message(
                "❌ No pude modificar la presencia del bot.",
                ephemeral=True
            )
# ================================================================
# SETUP
# ================================================================
async def setup(bot):
    await bot.add_cog(
        Presencia(bot)
    )