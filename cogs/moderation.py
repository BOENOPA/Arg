import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta
# ============================================================
# COLORES
# ============================================================
PURPLE = discord.Color.from_rgb(115, 55, 210)
GREEN = discord.Color.from_rgb(45, 190, 110)
RED = discord.Color.from_rgb(220, 60, 70)
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
# COG MODERACIÓN
# ============================================================
class Moderacion(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("========================================")
        print("🛡️ COG MODERACIÓN")
        print("========================================")
        print("✅ Moderación cargada correctamente")
        print("✅ /mute")
        print("✅ /lock")
        print("✅ /unlock")
        print("========================================")
    # ========================================================
    # MUTE
    # ========================================================
    @app_commands.command(
        name="mute",
        description="Silencia temporalmente a un miembro."
    )
    @app_commands.describe(
        usuario="Usuario que quieres silenciar",
        minutos="Duración del mute en minutos",
        razon="Razón del mute"
    )
    @app_commands.default_permissions(moderate_members=True)
    async def mute(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        minutos: app_commands.Range[int, 1, 40320],
        razon: str = "Sin razón especificada"
    ):
        print(
            f"[MUTE] {interaction.user} "
            f"intentó mutear a {usuario} por {minutos} minutos."
        )
        # ----------------------------------------------------
        # GUILD
        # ----------------------------------------------------
        if interaction.guild is None:
            await interaction.response.send_message(
                embed=error_embed(
                    "Este comando solamente puede utilizarse dentro de un servidor."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # PERMISOS DEL USUARIO
        # ----------------------------------------------------
        if not interaction.user.guild_permissions.moderate_members:
            print(
                f"[MUTE] ❌ {interaction.user} no tiene permiso."
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "Necesitas el permiso **Moderar miembros** para utilizar este comando."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # PERMISOS DEL BOT
        # ----------------------------------------------------
        if not interaction.guild.me.guild_permissions.moderate_members:
            print(
                "[MUTE] ❌ El bot no tiene permiso Moderar miembros."
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "No tengo el permiso **Moderar miembros**."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # NO MUTear AL PROPIO BOT
        # ----------------------------------------------------
        if usuario.id == self.bot.user.id:
            await interaction.response.send_message(
                embed=error_embed(
                    "No puedo silenciarme a mí mismo."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # JERARQUÍA
        # ----------------------------------------------------
        if usuario == interaction.user:
            await interaction.response.send_message(
                embed=error_embed(
                    "No puedes silenciarte a ti mismo."
                ),
                ephemeral=True
            )
            return
        if usuario.top_role >= interaction.user.top_role:
            await interaction.response.send_message(
                embed=error_embed(
                    "No puedes silenciar a alguien con un rol igual o superior al tuyo."
                ),
                ephemeral=True
            )
            return
        if usuario.top_role >= interaction.guild.me.top_role:
            print(
                "[MUTE] ❌ El rol del usuario está por encima del bot."
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "No puedo silenciar a ese usuario porque su rol está por encima de mi rol."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # MUTE
        # ----------------------------------------------------
        try:
            duracion = timedelta(minutes=minutos)
            await usuario.timeout(
                duracion,
                reason=razon
            )
            print(
                f"[MUTE] ✅ {usuario} fue silenciado "
                f"por {minutos} minutos."
            )
            embed = success_embed(
                "🔇 Usuario silenciado",
                f"**Usuario:** {usuario.mention}\n"
                f"**Duración:** `{minutos}` minutos\n"
                f"**Razón:** {razon}\n"
                f"**Moderador:** {interaction.user.mention}"
            )
            await interaction.response.send_message(
                embed=embed
            )
        except discord.Forbidden:
            print(
                "[MUTE] ❌ Discord rechazó la acción. "
                "Revisar permisos/jerarquía."
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "No tengo permisos suficientes para silenciar a ese usuario."
                ),
                ephemeral=True
            )
        except discord.HTTPException as e:
            print(
                f"[MUTE] ❌ Error HTTP: {e}"
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "Discord rechazó la operación."
                ),
                ephemeral=True
            )
        except Exception as e:
            print(
                f"[MUTE] ❌ Error inesperado: {repr(e)}"
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "Ocurrió un error inesperado."
                ),
                ephemeral=True
            )
    # ========================================================
    # LOCK
    # ========================================================
    @app_commands.command(
        name="lock",
        description="Bloquea el canal para todos excepto quien ejecuta el comando."
    )
    @app_commands.default_permissions(manage_channels=True)
    async def lock(
        self,
        interaction: discord.Interaction
    ):
        print("========================================")
        print("🔒 LOCK")
        print(f"👤 Usuario: {interaction.user}")
        print(f"🆔 ID: {interaction.user.id}")
        print("========================================")
        # ----------------------------------------------------
        # GUILD
        # ----------------------------------------------------
        if interaction.guild is None:
            print("[LOCK] ❌ No se ejecutó dentro de un servidor.")
            await interaction.response.send_message(
                embed=error_embed(
                    "Este comando solamente puede utilizarse dentro de un servidor."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # CANAL
        # ----------------------------------------------------
        canal = interaction.channel
        if not isinstance(canal, discord.TextChannel):
            print("[LOCK] ❌ El canal no es un canal de texto.")
            await interaction.response.send_message(
                embed=error_embed(
                    "Este comando solamente funciona en canales de texto."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # PERMISOS DEL USUARIO
        # ----------------------------------------------------
        if not interaction.user.guild_permissions.manage_channels:
            print(
                f"[LOCK] ❌ {interaction.user} no tiene Manage Channels."
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "Necesitas el permiso **Gestionar canales**."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # PERMISOS DEL BOT
        # ----------------------------------------------------
        me = interaction.guild.me
        if me is None:
            print("[LOCK] ❌ No pude obtener el miembro del bot.")
            await interaction.response.send_message(
                embed=error_embed(
                    "No pude comprobar mis permisos."
                ),
                ephemeral=True
            )
            return
        if not me.guild_permissions.manage_channels:
            print(
                "[LOCK] ❌ El bot no tiene Manage Channels."
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "Necesito el permiso **Gestionar canales**."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # @EVERYONE
        # ----------------------------------------------------
        everyone = interaction.guild.default_role
        print(
            f"[LOCK] 🔒 Bloqueando escritura para @everyone "
            f"en #{canal.name}..."
        )
        try:
            # =================================================
            # CAMBIO 1
            # Bloquea a todos mediante @everyone.
            # NO toca ningún otro rol.
            # =================================================
            await canal.set_permissions(
                everyone,
                send_messages=False
            )
            print(
                "[LOCK] ✅ @everyone bloqueado."
            )
            # =================================================
            # CAMBIO 2
            # Permite escribir únicamente al usuario que
            # ejecutó /lock.
            # =================================================
            await canal.set_permissions(
                interaction.user,
                send_messages=True
            )
            print(
                f"[LOCK] ✅ {interaction.user} puede escribir."
            )
            print(
                "[LOCK] 🚀 Canal bloqueado usando solamente "
                "@everyone + usuario."
            )
            # ------------------------------------------------
            # RESPUESTA
            # ------------------------------------------------
            embed = success_embed(
                "🔒 Canal bloqueado",
                f"El canal quedó bloqueado para todos.\n\n"
                f"✍️ **Solo puede escribir:** {interaction.user.mention}"
            )
            await interaction.response.send_message(
                embed=embed
            )
            print(
                "[LOCK] ✅ Operación completada."
            )
        except discord.Forbidden:
            print(
                "[LOCK] ❌ Discord rechazó el cambio de permisos."
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=error_embed(
                        "No tengo permisos suficientes para bloquear este canal."
                    ),
                    ephemeral=True
                )
        except discord.HTTPException as e:
            print(
                f"[LOCK] ❌ Error HTTP: {e}"
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=error_embed(
                        "Discord rechazó el cambio de permisos."
                    ),
                    ephemeral=True
                )
        except Exception as e:
            print(
                f"[LOCK] ❌ Error inesperado: {repr(e)}"
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=error_embed(
                        "Ocurrió un error inesperado al bloquear el canal."
                    ),
                    ephemeral=True
                )
    # ========================================================
    # UNLOCK
    # ========================================================
    @app_commands.command(
        name="unlock",
        description="Desbloquea el canal."
    )
    @app_commands.default_permissions(manage_channels=True)
    async def unlock(
        self,
        interaction: discord.Interaction
    ):
        print("========================================")
        print("🔓 UNLOCK")
        print(f"👤 Usuario: {interaction.user}")
        print(f"🆔 ID: {interaction.user.id}")
        print("========================================")
        # ----------------------------------------------------
        # GUILD
        # ----------------------------------------------------
        if interaction.guild is None:
            print("[UNLOCK] ❌ No se ejecutó dentro de un servidor.")
            await interaction.response.send_message(
                embed=error_embed(
                    "Este comando solamente puede utilizarse dentro de un servidor."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # CANAL
        # ----------------------------------------------------
        canal = interaction.channel
        if not isinstance(canal, discord.TextChannel):
            print("[UNLOCK] ❌ El canal no es de texto.")
            await interaction.response.send_message(
                embed=error_embed(
                    "Este comando solamente funciona en canales de texto."
                ),
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # PERMISOS
        # ----------------------------------------------------
        if not interaction.user.guild_permissions.manage_channels:
            print(
                f"[UNLOCK] ❌ {interaction.user} no tiene Manage Channels."
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "Necesitas el permiso **Gestionar canales**."
                ),
                ephemeral=True
            )
            return
        me = interaction.guild.me
        if me is None or not me.guild_permissions.manage_channels:
            print(
                "[UNLOCK] ❌ El bot no tiene Manage Channels."
            )
            await interaction.response.send_message(
                embed=error_embed(
                    "Necesito el permiso **Gestionar canales**."
                ),
                ephemeral=True
            )
            return
        everyone = interaction.guild.default_role
        try:
            print(
                f"[UNLOCK] 🔓 Restaurando @everyone en #{canal.name}..."
            )
            # =================================================
            # QUITA EL DENY DE @everyone
            # =================================================
            await canal.set_permissions(
                everyone,
                send_messages=None
            )
            print(
                "[UNLOCK] ✅ @everyone restaurado."
            )
            # =================================================
            # QUITA EL OVERWRITE DEL USUARIO QUE EJECUTA
            # =================================================
            await canal.set_permissions(
                interaction.user,
                send_messages=None
            )
            print(
                "[UNLOCK] ✅ Overwrite del usuario eliminado."
            )
            embed = success_embed(
                "🔓 Canal desbloqueado",
                "El canal volvió a permitir escribir normalmente."
            )
            await interaction.response.send_message(
                embed=embed
            )
            print(
                "[UNLOCK] 🚀 Canal desbloqueado correctamente."
            )
        except discord.Forbidden:
            print(
                "[UNLOCK] ❌ Discord rechazó el cambio de permisos."
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=error_embed(
                        "No tengo permisos suficientes para desbloquear este canal."
                    ),
                    ephemeral=True
                )
        except discord.HTTPException as e:
            print(
                f"[UNLOCK] ❌ Error HTTP: {e}"
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=error_embed(
                        "Discord rechazó el cambio de permisos."
                    ),
                    ephemeral=True
                )
        except Exception as e:
            print(
                f"[UNLOCK] ❌ Error inesperado: {repr(e)}"
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    embed=error_embed(
                        "Ocurrió un error inesperado."
                    ),
                    ephemeral=True
                )
# ============================================================
# SETUP
# ============================================================
async def setup(bot: commands.Bot):
    await bot.add_cog(Moderacion(bot))
    print("🛡️ [MODERACIÓN] Cog cargado correctamente.")