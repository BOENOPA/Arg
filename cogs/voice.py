import discord
from discord import app_commands
from discord.ext import commands
# ============================================================
# COLORES
# ============================================================
PURPLE = discord.Color.from_rgb(115, 55, 210)
RED = discord.Color.from_rgb(220, 60, 70)
GREEN = discord.Color.from_rgb(45, 190, 110)
# ============================================================
# EMBEDS
# ============================================================
def error_embed(text: str):
    return discord.Embed(
        description=f"❌ {text}",
        color=RED
    )
def success_embed(title: str, description: str):
    return discord.Embed(
        title=title,
        description=description,
        color=PURPLE
    )
# ============================================================
# COG VOICE
# ============================================================
class Voice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("========================================")
        print("🔊 COG VOICE")
        print("========================================")
        print("✅ Voice cargado correctamente")
        print("✅ /vc")
        print("✅ /vcsalir")
        print("========================================")
    # ========================================================
    # /VC
    # ========================================================
    @app_commands.command(
        name="vc",
        description="Hace que el bot entre a tu canal de voz."
    )
    async def vc(self, interaction: discord.Interaction):
        print("========================================")
        print("🔊 COMANDO /VC")
        print(f"👤 Usuario: {interaction.user}")
        print(f"🆔 ID: {interaction.user.id}")
        print("========================================")
        # ----------------------------------------------------
        # COMPROBAR SERVIDOR
        # ----------------------------------------------------
        if interaction.guild is None:
            print("[VC] ❌ No se ejecutó dentro de un servidor.")
            await interaction.response.send_message(
                embed=error_embed(
                    "Este comando solamente puede utilizarse dentro de un servidor."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # COMPROBAR SI EL USUARIO ESTÁ EN VOZ
        # ----------------------------------------------------
        if not isinstance(interaction.user, discord.Member):
            print("[VC] ❌ No se pudo obtener el miembro.")
            await interaction.response.send_message(
                embed=error_embed(
                    "No pude obtener tu información dentro del servidor."
                ),
                ephemeral=True
            )
            return
        canal_voz = interaction.user.voice.channel if interaction.user.voice else None
        if canal_voz is None:
            print(
                f"[VC] ❌ {interaction.user} no está conectado a un canal de voz."
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "Tenés que estar conectado a un canal de voz primero."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # COMPROBAR PERMISOS DEL BOT
        # ----------------------------------------------------
        me = interaction.guild.me
        if me is None:
            print("[VC] ❌ No pude obtener al bot como miembro.")
            await interaction.response.send_message(
                embed=error_embed(
                    "No pude comprobar mis permisos."
                ),
                ephemeral=True
            )
            return
        permisos = canal_voz.permissions_for(me)
        if not permisos.connect:
            print(
                f"[VC] ❌ No puedo conectarme a #{canal_voz.name}."
            )
            await interaction.response.send_message(
                embed=error_embed(
                    f"No tengo permiso para conectarme a **{canal_voz.name}**."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # SI YA ESTÁ CONECTADO
        # ----------------------------------------------------
        voice_client = interaction.guild.voice_client
        try:
            # =================================================
            # YA ESTÁ EN EL MISMO CANAL
            # =================================================
            if voice_client and voice_client.channel == canal_voz:
                print(
                    f"[VC] ℹ️ Ya estoy conectado a #{canal_voz.name}."
                )
                await interaction.response.send_message(
                    embed=success_embed(
                        "🔊 Ya estoy en el VC",
                        f"Ya estoy conectado a {canal_voz.mention}."
                    ),
                    ephemeral=True
                )
                return
            # =================================================
            # ESTÁ EN OTRO CANAL → MOVER
            # =================================================
            if voice_client:
                print(
                    f"[VC] 🔄 Moviendo bot de "
                    f"#{voice_client.channel.name} → #{canal_voz.name}"
                )
                await voice_client.move_to(canal_voz)
                print(
                    f"[VC] ✅ Bot movido a #{canal_voz.name}"
                )
            # =================================================
            # NO ESTÁ CONECTADO → ENTRAR
            # =================================================
            else:
                print(
                    f"[VC] 🔊 Entrando a #{canal_voz.name}..."
                )
                await canal_voz.connect(
                    self_deaf=True,
                    self_mute=False
                )
                print(
                    f"[VC] ✅ Bot conectado a #{canal_voz.name}"
                )
            # ------------------------------------------------
            # RESPUESTA
            # ------------------------------------------------
            await interaction.response.send_message(
                embed=success_embed(
                    "🔊 Conectado al VC",
                    f"Entré a {canal_voz.mention}.\n\n"
                    f"Usá **/vcsalir** cuando quieras que salga."
                ),
                ephemeral=True
            )
            print(
                "[VC] 🚀 Operación completada correctamente."
            )
        except discord.ClientException as e:
            print(
                f"[VC] ❌ ClientException: {repr(e)}"
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "No pude conectarme al canal de voz."
                ),
                ephemeral=True
            )
        except discord.Forbidden as e:
            print(
                f"[VC] ❌ Forbidden: {repr(e)}"
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "Discord no me permite conectarme a ese canal."
                ),
                ephemeral=True
            )
        except discord.HTTPException as e:
            print(
                f"[VC] ❌ HTTPException: {repr(e)}"
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "Discord rechazó la conexión al canal de voz."
                ),
                ephemeral=True
            )
        except Exception as e:
            print(
                f"[VC] ❌ Error inesperado: {repr(e)}"
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "Ocurrió un error inesperado."
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
        print("========================================")
        print("🔇 COMANDO /VCSALIR")
        print(f"👤 Usuario: {interaction.user}")
        print(f"🆔 ID: {interaction.user.id}")
        print("========================================")
        # ----------------------------------------------------
        # COMPROBAR SERVIDOR
        # ----------------------------------------------------
        if interaction.guild is None:
            print("[VCSALIR] ❌ No se ejecutó dentro de un servidor.")
            await interaction.response.send_message(
                embed=error_embed(
                    "Este comando solamente puede utilizarse dentro de un servidor."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # COMPROBAR CONEXIÓN
        # ----------------------------------------------------
        voice_client = interaction.guild.voice_client
        if voice_client is None:
            print(
                "[VCSALIR] ℹ️ El bot no está conectado a ningún VC."
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "No estoy conectado a ningún canal de voz."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # SALIR
        # ----------------------------------------------------
        canal_actual = voice_client.channel
        try:
            print(
                f"[VCSALIR] 🔇 Saliendo de #{canal_actual.name}..."
            )
            await voice_client.disconnect()
            print(
                f"[VCSALIR] ✅ Bot salió de #{canal_actual.name}."
            )
            await interaction.response.send_message(
                embed=success_embed(
                    "🔇 Salí del VC",
                    f"Salí de **{canal_actual.name}** correctamente."
                ),
                ephemeral=True
            )
            print(
                "[VCSALIR] 🚀 Operación completada correctamente."
            )
        except discord.HTTPException as e:
            print(
                f"[VCSALIR] ❌ HTTPException: {repr(e)}"
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "Discord rechazó la desconexión."
                ),
                ephemeral=True
            )
        except Exception as e:
            print(
                f"[VCSALIR] ❌ Error inesperado: {repr(e)}"
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "Ocurrió un error al salir del canal."
                ),
                ephemeral=True
            )
# ============================================================
# SETUP
# ============================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(Voice(bot))
    print("🔊 [VOICE] Cog cargado correctamente.")