import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta
# ============================================================
# CONFIGURACIÓN
# ============================================================
PURPLE = discord.Color.from_rgb(115, 55, 210)
RED = discord.Color.from_rgb(220, 60, 70)
GREEN = discord.Color.from_rgb(45, 190, 110)
# ============================================================
# UTILIDADES
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
# COG
# ============================================================
class Moderacion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    # ========================================================
    # MUTE
    # ========================================================
    @app_commands.command(
        name="mute",
        description="Silencia temporalmente a un usuario."
    )
    @app_commands.describe(
        usuario="Usuario que querés silenciar",
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
        # ----------------------------------------------------
        # COMPROBACIÓN DE SERVIDOR
        # ----------------------------------------------------
        if interaction.guild is None:
            return await interaction.response.send_message(
                embed=error_embed(
                    "Este comando solamente puede utilizarse dentro de un servidor."
                ),
                ephemeral=True
            )
        # ----------------------------------------------------
        # COMPROBACIÓN DE PERMISOS DEL USUARIO
        # ----------------------------------------------------
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message(
                embed=error_embed(
                    "No tenés permisos para silenciar miembros."
                ),
                ephemeral=True
            )
        # ----------------------------------------------------
        # COMPROBACIÓN DE PERMISOS DEL BOT
        # ----------------------------------------------------
        if not interaction.guild.me.guild_permissions.moderate_members:
            return await interaction.response.send_message(
                embed=error_embed(
                    "No tengo el permiso **Moderate Members**."
                ),
                ephemeral=True
            )
        # ----------------------------------------------------
        # NO AUTO-MUTE
        # ----------------------------------------------------
        if usuario.id == interaction.user.id:
            return await interaction.response.send_message(
                embed=error_embed(
                    "No podés silenciarte a vos mismo."
                ),
                ephemeral=True
            )
        # ----------------------------------------------------
        # NO MUTEEAR AL DUEÑO
        # ----------------------------------------------------
        if usuario.id == interaction.guild.owner_id:
            return await interaction.response.send_message(
                embed=error_embed(
                    "No podés silenciar al dueño del servidor."
                ),
                ephemeral=True
            )
        # ----------------------------------------------------
        # JERARQUÍA DEL MODERADOR
        # ----------------------------------------------------
        if (
            interaction.user.id != interaction.guild.owner_id
            and usuario.top_role >= interaction.user.top_role
        ):
            return await interaction.response.send_message(
                embed=error_embed(
                    "No podés silenciar a alguien que tiene un rol igual o superior al tuyo."
                ),
                ephemeral=True
            )
        # ----------------------------------------------------
        # JERARQUÍA DEL BOT
        # ----------------------------------------------------
        if usuario.top_role >= interaction.guild.me.top_role:
            return await interaction.response.send_message(
                embed=error_embed(
                    "No puedo silenciar a ese usuario porque su rol está por encima o al mismo nivel que mi rol."
                ),
                ephemeral=True
            )
        # ----------------------------------------------------
        # COMPROBACIÓN MODERATABLE
        # ----------------------------------------------------
        if not usuario.moderatable:
            return await interaction.response.send_message(
                embed=error_embed(
                    "No puedo moderar a ese usuario con mis permisos actuales."
                ),
                ephemeral=True
            )
        # ----------------------------------------------------
        # EJECUTAR MUTE
        # ----------------------------------------------------
        try:
            duracion = timedelta(minutes=minutos)
            await usuario.timeout(
                duracion,
                reason=f"{razon} | Moderador: {interaction.user}"
            )
            embed = success_embed(
                "🔇 Usuario silenciado",
                f"{usuario.mention} fue silenciado correctamente."
            )
            embed.add_field(
                name="⏱️ Duración",
                value=f"`{minutos}` minutos",
                inline=True
            )
            embed.add_field(
                name="👤 Moderador",
                value=interaction.user.mention,
                inline=True
            )
            embed.add_field(
                name="📝 Razón",
                value=razon,
                inline=False
            )
            embed.set_footer(
                text=f"ID del usuario: {usuario.id}"
            )
            await interaction.response.send_message(
                embed=embed
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=error_embed(
                    "Discord rechazó la acción. Revisá los permisos y la posición de mi rol."
                ),
                ephemeral=True
            )
        except discord.HTTPException:
            await interaction.response.send_message(
                embed=error_embed(
                    "Discord devolvió un error al intentar silenciar al usuario."
                ),
                ephemeral=True
            )
        except Exception as e:
            print(f"[MUTE] Error: {e}")
            await interaction.response.send_message(
                embed=error_embed(
                    "Ocurrió un error inesperado al intentar silenciar al usuario."
                ),
                ephemeral=True
            )
    # ========================================================
    # LOCK
    # ========================================================
    @app_commands.command(
        name="lock",
        description="Bloquea el canal actual."
    )
    @app_commands.default_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction):
        # ----------------------------------------------------
        # SERVIDOR
        # ----------------------------------------------------
        if interaction.guild is None:
            return await interaction.response.send_message(
                embed=error_embed(
                    "Este comando solamente puede utilizarse dentro de un servidor."
                ),
                ephemeral=True
            )
        # ----------------------------------------------------
        # PERMISOS DEL USUARIO
        # ----------------------------------------------------
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message(
                embed=error_embed(
                    "No tenés permisos para administrar canales."
                ),
                ephemeral=True
            )
        # ----------------------------------------------------
        # PERMISOS DEL BOT
        # ----------------------------------------------------
        if not interaction.guild.me.guild_permissions.manage_channels:
            return await interaction.response.send_message(
                embed=error_embed(
                    "No tengo el permiso **Manage Channels**."
                ),
                ephemeral=True
            )
        # ----------------------------------------------------
        # TIPO DE CANAL
        # ----------------------------------------------------
        canal = interaction.channel
        if not isinstance(canal, discord.TextChannel):
            return await interaction.response.send_message(
                embed=error_embed(
                    "Este comando solamente funciona en canales de texto."
                ),
                ephemeral=True
            )
        # ----------------------------------------------------
        # LOCK
        # ----------------------------------------------------
        try:
            everyone = interaction.guild.default_role
            await canal.set_permissions(
                everyone,
                send_messages=False,
                reason=f"Canal bloqueado por {interaction.user}"
            )
            embed = success_embed(
                "🔒 Canal bloqueado",
                (
                    f"{canal.mention} fue bloqueado correctamente.\n"
                    "Los miembros ya no pueden enviar mensajes."
                )
            )
            embed.set_footer(
                text=f"Bloqueado por {interaction.user}"
            )
            await interaction.response.send_message(
                embed=embed
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=error_embed(
                    "No puedo modificar los permisos de este canal."
                ),
                ephemeral=True
            )
        except discord.HTTPException:
            await interaction.response.send_message(
                embed=error_embed(
                    "Discord devolvió un error al bloquear el canal."
                ),
                ephemeral=True
            )
        except Exception as e:
            print(f"[LOCK] Error: {e}")
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
        description="Desbloquea el canal actual."
    )
    @app_commands.default_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction):
        # ----------------------------------------------------
        # SERVIDOR
        # ----------------------------------------------------
        if interaction.guild is None:
            return await interaction.response.send_message(
                embed=error_embed(
                    "Este comando solamente puede utilizarse dentro de un servidor."
                ),
                ephemeral=True
            )
        # ----------------------------------------------------
        # PERMISOS DEL USUARIO
        # ----------------------------------------------------
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message(
                embed=error_embed(
                    "No tenés permisos para administrar canales."
                ),
                ephemeral=True
            )
        # ----------------------------------------------------
        # PERMISOS DEL BOT
        # ----------------------------------------------------
        if not interaction.guild.me.guild_permissions.manage_channels:
            return await interaction.response.send_message(
                embed=error_embed(
                    "No tengo el permiso **Manage Channels**."
                ),
                ephemeral=True
            )
        # ----------------------------------------------------
        # TIPO DE CANAL
        # ----------------------------------------------------
        canal = interaction.channel
        if not isinstance(canal, discord.TextChannel):
            return await interaction.response.send_message(
                embed=error_embed(
                    "Este comando solamente funciona en canales de texto."
                ),
                ephemeral=True
            )
        # ----------------------------------------------------
        # UNLOCK
        # ----------------------------------------------------
        try:
            everyone = interaction.guild.default_role
            await canal.set_permissions(
                everyone,
                send_messages=None,
                reason=f"Canal desbloqueado por {interaction.user}"
            )
            embed = discord.Embed(
                title="🔓 Canal desbloqueado",
                description=(
                    f"{canal.mention} fue desbloqueado correctamente.\n"
                    "Los miembros pueden volver a enviar mensajes."
                ),
                color=GREEN
            )
            embed.set_footer(
                text=f"Desbloqueado por {interaction.user}"
            )
            await interaction.response.send_message(
                embed=embed
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=error_embed(
                    "No puedo modificar los permisos de este canal."
                ),
                ephemeral=True
            )
        except discord.HTTPException:
            await interaction.response.send_message(
                embed=error_embed(
                    "Discord devolvió un error al desbloquear el canal."
                ),
                ephemeral=True
            )
        except Exception as e:
            print(f"[UNLOCK] Error: {e}")
            await interaction.response.send_message(
                embed=error_embed(
                    "Ocurrió un error inesperado al desbloquear el canal."
                ),
                ephemeral=True
            )
# ============================================================
# SETUP
# ============================================================
async def setup(bot):
    await bot.add_cog(Moderacion(bot))

Permisos

Comando	Permiso del usuario	Permiso del bot
/mute	Moderate Members	Moderate Members
/lock	Manage Channels	Manage Channels
/unlock	Manage Channels	Manage Channels

Además, /mute comprueba la jerarquía de roles, por lo que ni el moderador ni el bot pueden actuar sobre miembros que estén por encima de ellos.