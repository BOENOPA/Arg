import discord
from discord import app_commands
from discord.ext import commands
# ============================================================
# COLORES
# ============================================================
PURPLE = discord.Color.from_rgb(115, 55, 210)
GREEN = discord.Color.from_rgb(45, 190, 110)
RED = discord.Color.from_rgb(220, 60, 70)
# ============================================================
# EMBEDS
# ============================================================
def error_embed(text):
    return discord.Embed(
        description=f"❌ {text}",
        color=RED
    )
def success_embed(title, text):
    embed = discord.Embed(
        title=title,
        description=text,
        color=PURPLE
    )
    return embed
# ============================================================
# VOICE COG
# ============================================================
class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("🔊 [VOICE] Cog iniciado")
        print("🔊 [VOICE] Comando /vc")
        print("🔊 [VOICE] Comando /vcsalir")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    # ========================================================
    # /VC
    # ========================================================
    @app_commands.command(
        name="vc",
        description="Hace que el bot entre a tu canal de voz."
    )
    async def vc(self, interaction: discord.Interaction):
        print(
            f"🔊 [VOICE] /vc ejecutado por "
            f"{interaction.user} ({interaction.user.id})"
        )
        # ----------------------------------------------------
        # SERVIDOR
        # ----------------------------------------------------
        if interaction.guild is None:
            print("❌ [VOICE] Comando usado fuera de un servidor.")
            await interaction.response.send_message(
                embed=error_embed(
                    "Este comando solamente se puede usar dentro de un servidor."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # USUARIO
        # ----------------------------------------------------
        member = interaction.guild.get_member(interaction.user.id)
        if member is None:
            print("❌ [VOICE] No se pudo obtener el miembro.")
            await interaction.response.send_message(
                embed=error_embed(
                    "No pude encontrar tu usuario en el servidor."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # CANAL DEL USUARIO
        # ----------------------------------------------------
        if member.voice is None or member.voice.channel is None:
            print(
                f"❌ [VOICE] {interaction.user} no está en un canal de voz."
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "Tenés que estar conectado a un canal de voz primero."
                ),
                ephemeral=True
            )
            return
        canal = member.voice.channel
        print(
            f"🎙️ [VOICE] Canal solicitado: "
            f"{canal.name} ({canal.id})"
        )
        # ----------------------------------------------------
        # BOT
        # ----------------------------------------------------
        bot_member = interaction.guild.me
        if bot_member is None:
            print("❌ [VOICE] No se pudo obtener al bot.")
            await interaction.response.send_message(
                embed=error_embed(
                    "No pude obtener mis permisos dentro del servidor."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # PERMISOS
        # ----------------------------------------------------
        permisos = canal.permissions_for(bot_member)
        print(
            f"🔐 [VOICE] Permisos - "
            f"connect={permisos.connect} | "
            f"view_channel={permisos.view_channel}"
        )
        if not permisos.view_channel:
            print("❌ [VOICE] El bot no puede ver el canal.")
            await interaction.response.send_message(
                embed=error_embed(
                    "No tengo permiso para ver ese canal de voz."
                ),
                ephemeral=True
            )
            return
        if not permisos.connect:
            print("❌ [VOICE] El bot no puede conectarse al canal.")
            await interaction.response.send_message(
                embed=error_embed(
                    "No tengo permiso para conectarme a ese canal de voz."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # VOICE CLIENT ACTUAL
        # ----------------------------------------------------
        voice_client = interaction.guild.voice_client
        # ----------------------------------------------------
        # YA ESTÁ EN ESE CANAL
        # ----------------------------------------------------
        if voice_client is not None:
            print(
                f"🔊 [VOICE] Ya existe una conexión."
            )
            print(
                f"🔊 [VOICE] Canal actual: "
                f"{voice_client.channel}"
            )
            if voice_client.channel.id == canal.id:
                print(
                    "ℹ️ [VOICE] El bot ya está en el canal solicitado."
                )
                await interaction.response.send_message(
                    embed=success_embed(
                        "🔊 Ya estoy acá",
                        f"Ya estoy conectado a {canal.mention}."
                    ),
                    ephemeral=True
                )
                return
            # ------------------------------------------------
            # MOVER BOT
            # ------------------------------------------------
            try:
                print(
                    f"🔄 [VOICE] Moviendo bot a {canal.name}..."
                )
                await voice_client.move_to(canal)
                print(
                    f"✅ [VOICE] Bot movido correctamente a "
                    f"{canal.name}"
                )
                await interaction.response.send_message(
                    embed=success_embed(
                        "🔊 Canal cambiado",
                        f"Me moví a {canal.mention}."
                    )
                )
                return
            except Exception as e:
                print(
                    f"❌ [VOICE] Error moviendo el bot: "
                    f"{type(e).__name__}: {e}"
                )
                await interaction.response.send_message(
                    embed=error_embed(
                        f"No pude moverme al canal.\n"
                        f"`{type(e).__name__}`"
                    ),
                    ephemeral=True
                )
                return
        # ----------------------------------------------------
        # CONECTAR
        # ----------------------------------------------------
        try:
            print(
                f"🔌 [VOICE] Intentando conectar a {canal.name}..."
            )
            voice_client = await canal.connect(
                timeout=30,
                reconnect=True,
                self_deaf=True,
                self_mute=False
            )
            print(
                f"✅ [VOICE] Conectado correctamente."
            )
            print(
                f"🔊 [VOICE] VoiceClient: {voice_client}"
            )
            print(
                f"🔊 [VOICE] Canal: {voice_client.channel}"
            )
            print(
                f"🔊 [VOICE] Estado conectado: "
                f"{voice_client.is_connected()}"
            )
            await interaction.response.send_message(
                embed=success_embed(
                    "🔊 Conectado",
                    f"Me conecté a {canal.mention}.\n\n"
                    "Me voy a quedar conectado hasta que uses "
                    "`/vcsalir`."
                )
            )
        except discord.Forbidden:
            print(
                "❌ [VOICE] Discord rechazó la conexión "
                "(Forbidden)."
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "Discord rechazó la conexión. "
                    "Revisá mis permisos para conectarme al canal."
                ),
                ephemeral=True
            )
        except discord.ClientException as e:
            print(
                f"❌ [VOICE] ClientException: {e}"
            )
            await interaction.response.send_message(
                embed=error_embed(
                    f"Discord.py no pudo establecer la conexión.\n"
                    f"`{e}`"
                ),
                ephemeral=True
            )
        except Exception as e:
            print(
                f"❌ [VOICE] ERROR CRÍTICO: "
                f"{type(e).__name__}: {e}"
            )
            await interaction.response.send_message(
                embed=error_embed(
                    f"Ocurrió un error al conectarme.\n"
                    f"`{type(e).__name__}`"
                ),
                ephemeral=True
            )
    # ========================================================
    # /VCSALIR
    # ========================================================
    @app_commands.command(
        name="vcsalir",
        description="Hace que el bot salga del canal de voz."
    )
    async def vcsalir(self, interaction: discord.Interaction):
        print(
            f"🔊 [VOICE] /vcsalir ejecutado por "
            f"{interaction.user} ({interaction.user.id})"
        )
        if interaction.guild is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "Este comando solamente se puede usar dentro de un servidor."
                ),
                ephemeral=True
            )
            return
        voice_client = interaction.guild.voice_client
        if voice_client is None:
            print(
                "ℹ️ [VOICE] El bot no está conectado a ningún canal."
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "No estoy conectado a ningún canal de voz."
                ),
                ephemeral=True
            )
            return
        try:
            canal_anterior = voice_client.channel
            print(
                f"🔌 [VOICE] Desconectando de "
                f"{canal_anterior.name}..."
            )
            await voice_client.disconnect(force=True)
            print(
                "✅ [VOICE] Bot desconectado correctamente."
            )
            await interaction.response.send_message(
                embed=success_embed(
                    "🔌 Desconectado",
                    "Salí del canal de voz correctamente."
                )
            )
        except Exception as e:
            print(
                f"❌ [VOICE] Error desconectando: "
                f"{type(e).__name__}: {e}"
            )
            await interaction.response.send_message(
                embed=error_embed(
                    f"No pude salir del canal.\n"
                    f"`{type(e).__name__}`"
                ),
                ephemeral=True
            )
# ============================================================
# SETUP
# ============================================================
async def setup(bot):
    await bot.add_cog(Voice(bot))
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✅ [VOICE] Cog cargado correctamente.")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")