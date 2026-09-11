import os
import json
import discord
from discord import app_commands
from discord.ext import commands
# ============================================================
# CONFIGURACIÓN
# ============================================================
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "logs.json")
os.makedirs(DATA_DIR, exist_ok=True)
# ============================================================
# BASE DE DATOS
# ============================================================
def cargar_datos():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
def guardar_datos(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )
# ============================================================
# UTILIDADES
# ============================================================
def get_guild_data(data, guild_id):
    guild_id = str(guild_id)
    if guild_id not in data:
        data[guild_id] = {
            "channel_id": None
        }
    return data[guild_id]
# ============================================================
# COG
# ============================================================
class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = cargar_datos()
        # Cache para detectar cambios de avatar/nickname/roles
        self.member_cache = {}
    # ========================================================
    # OBTENER CANAL DE LOGS
    # ========================================================
    def get_log_channel(self, guild):
        guild_data = get_guild_data(
            self.data,
            guild.id
        )
        channel_id = guild_data.get(
            "channel_id"
        )
        if not channel_id:
            return None
        return guild.get_channel(
            channel_id
        )
    # ========================================================
    # ENVIAR LOG
    # ========================================================
    async def enviar_log(
        self,
        guild,
        embed
    ):
        channel = self.get_log_channel(
            guild
        )
        if channel is None:
            return
        try:
            await channel.send(
                embed=embed
            )
        except (
            discord.Forbidden,
            discord.HTTPException
        ):
            pass
    # ========================================================
    # CONFIGLOGS
    # ========================================================
    @app_commands.command(
        name="configlogs",
        description="Configura el canal donde se enviarán los logs."
    )
    @app_commands.describe(
        canal="Canal donde se enviarán los registros."
    )
    async def configlogs(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel
    ):
        if not (
            interaction.user.guild_permissions.administrator
            or interaction.user.guild_permissions.manage_guild
        ):
            await interaction.response.send_message(
                "❌ Necesitás **Administrador** o "
                "**Gestionar servidor**.",
                ephemeral=True
            )
            return
        guild_data = get_guild_data(
            self.data,
            interaction.guild.id
        )
        guild_data["channel_id"] = canal.id
        guardar_datos(
            self.data
        )
        embed = discord.Embed(
            title="📋 Sistema de Logs",
            description=(
                f"Los registros del servidor serán enviados "
                f"a {canal.mention}."
            ),
            color=discord.Color.purple()
        )
        embed.add_field(
            name="Eventos registrados",
            value=(
                "🟢 Entradas\n"
                "🔴 Salidas\n"
                "🗑️ Mensajes eliminados\n"
                "✏️ Mensajes editados\n"
                "🖼️ Cambios de avatar\n"
                "🎭 Roles agregados\n"
                "➖ Roles quitados\n"
                "🏷️ Nicknames\n"
                "🔨 Baneos\n"
                "🔓 Desbaneos\n"
                "🎨 Roles\n"
                "📁 Canales"
            ),
            inline=False
        )
        await interaction.response.send_message(
            embed=embed
        )
    # ========================================================
    # MIEMBRO ENTRA
    # ========================================================
    @commands.Cog.listener()
    async def on_member_join(
        self,
        member
    ):
        embed = discord.Embed(
            title="🟢 Miembro ingresó",
            description=(
                f"{member.mention} ingresó al servidor."
            ),
            color=discord.Color.green()
        )
        embed.add_field(
            name="Usuario",
            value=(
                f"{member} (`{member.id}`)"
            ),
            inline=False
        )
        embed.add_field(
            name="Cuenta creada",
            value=discord.utils.format_dt(
                member.created_at,
                style="F"
            ),
            inline=False
        )
        if member.avatar:
            embed.set_thumbnail(
                url=member.avatar.url
            )
        embed.set_footer(
            text=f"ID: {member.id}"
        )
        await self.enviar_log(
            member.guild,
            embed
        )
    # ========================================================
    # MIEMBRO SALE
    # ========================================================
    @commands.Cog.listener()
    async def on_member_remove(
        self,
        member
    ):
        embed = discord.Embed(
            title="🔴 Miembro salió",
            description=(
                f"**{member}** abandonó el servidor."
            ),
            color=discord.Color.red()
        )
        embed.add_field(
            name="Usuario",
            value=(
                f"{member} (`{member.id}`)"
            ),
            inline=False
        )
        if member.avatar:
            embed.set_thumbnail(
                url=member.avatar.url
            )
        embed.set_footer(
            text=f"ID: {member.id}"
        )
        await self.enviar_log(
            member.guild,
            embed
        )
    # ========================================================
    # MENSAJE ELIMINADO
    # ========================================================
    @commands.Cog.listener()
    async def on_message_delete(
        self,
        message
    ):
        if message.guild is None:
            return
        if message.author.bot:
            return
        contenido = (
            message.content
            if message.content
            else "*Sin contenido de texto*"
        )
        if len(contenido) > 1000:
            contenido = (
                contenido[:1000]
                + "..."
            )
        embed = discord.Embed(
            title="🗑️ Mensaje eliminado",
            description=contenido,
            color=discord.Color.red()
        )
        embed.add_field(
            name="Autor",
            value=(
                f"{message.author.mention}\n"
                f"`{message.author.id}`"
            ),
            inline=True
        )
        embed.add_field(
            name="Canal",
            value=message.channel.mention,
            inline=True
        )
        if message.attachments:
            archivos = "\n".join(
                attachment.filename
                for attachment in message.attachments
            )
            embed.add_field(
                name="Archivos",
                value=archivos[:1000],
                inline=False
            )
        await self.enviar_log(
            message.guild,
            embed
        )
    # ========================================================
    # MENSAJE EDITADO
    # ========================================================
    @commands.Cog.listener()
    async def on_message_edit(
        self,
        before,
        after
    ):
        if before.guild is None:
            return
        if before.author.bot:
            return
        if before.content == after.content:
            return
        antes = (
            before.content
            if before.content
            else "*Vacío*"
        )
        despues = (
            after.content
            if after.content
            else "*Vacío*"
        )
        if len(antes) > 700:
            antes = antes[:700] + "..."
        if len(despues) > 700:
            despues = despues[:700] + "..."
        embed = discord.Embed(
            title="✏️ Mensaje editado",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="Usuario",
            value=before.author.mention,
            inline=False
        )
        embed.add_field(
            name="Canal",
            value=before.channel.mention,
            inline=False
        )
        embed.add_field(
            name="Antes",
            value=antes,
            inline=False
        )
        embed.add_field(
            name="Después",
            value=despues,
            inline=False
        )
        await self.enviar_log(
            before.guild,
            embed
        )
    # ========================================================
    # CAMBIOS DE MIEMBRO
    # ========================================================
    @commands.Cog.listener()
    async def on_member_update(
        self,
        before,
        after
    ):
        # ----------------------------------------------------
        # AVATAR
        # ----------------------------------------------------
        before_avatar = (
            before.avatar.url
            if before.avatar
            else None
        )
        after_avatar = (
            after.avatar.url
            if after.avatar
            else None
        )
        if before_avatar != after_avatar:
            embed = discord.Embed(
                title="🖼️ Avatar actualizado",
                description=(
                    f"{after.mention} cambió su avatar."
                ),
                color=discord.Color.purple()
            )
            if before.avatar:
                embed.set_thumbnail(
                    url=before.avatar.url
                )
            if after.avatar:
                embed.set_image(
                    url=after.avatar.url
                )
            embed.set_footer(
                text=f"ID: {after.id}"
            )
            await self.enviar_log(
                after.guild,
                embed
            )
        # ----------------------------------------------------
        # NICKNAME
        # ----------------------------------------------------
        if before.nick != after.nick:
            antes = before.nick or before.name
            despues = after.nick or after.name
            embed = discord.Embed(
                title="🏷️ Nickname actualizado",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Usuario",
                value=after.mention,
                inline=False
            )
            embed.add_field(
                name="Antes",
                value=f"`{antes}`",
                inline=True
            )
            embed.add_field(
                name="Después",
                value=f"`{despues}`",
                inline=True
            )
            await self.enviar_log(
                after.guild,
                embed
            )
        # ----------------------------------------------------
        # ROLES
        # ----------------------------------------------------
        roles_antes = set(
            before.roles
        )
        roles_despues = set(
            after.roles
        )
        agregados = roles_despues - roles_antes
        quitados = roles_antes - roles_despues
        for role in agregados:
            if role.is_default():
                continue
            embed = discord.Embed(
                title="🎭 Rol agregado",
                description=(
                    f"{after.mention} recibió el rol "
                    f"{role.mention}."
                ),
                color=discord.Color.green()
            )
            embed.add_field(
                name="Rol",
                value=(
                    f"{role.name}\n"
                    f"`{role.id}`"
                ),
                inline=False
            )
            await self.enviar_log(
                after.guild,
                embed
            )
        for role in quitados:
            if role.is_default():
                continue
            embed = discord.Embed(
                title="➖ Rol removido",
                description=(
                    f"A {after.mention} le quitaron "
                    f"el rol {role.mention}."
                ),
                color=discord.Color.red()
            )
            embed.add_field(
                name="Rol",
                value=(
                    f"{role.name}\n"
                    f"`{role.id}`"
                ),
                inline=False
            )
            await self.enviar_log(
                after.guild,
                embed
            )
    # ========================================================
    # BAN
    # ========================================================
    @commands.Cog.listener()
    async def on_member_ban(
        self,
        guild,
        user
    ):
        embed = discord.Embed(
            title="🔨 Usuario baneado",
            description=(
                f"**{user}** fue baneado del servidor."
            ),
            color=discord.Color.dark_red()
        )
        embed.add_field(
            name="Usuario",
            value=(
                f"{user.mention}\n"
                f"`{user.id}`"
            ),
            inline=False
        )
        await self.enviar_log(
            guild,
            embed
        )
    # ========================================================
    # UNBAN
    # ========================================================
    @commands.Cog.listener()
    async def on_member_unban(
        self,
        guild,
        user
    ):
        embed = discord.Embed(
            title="🔓 Usuario desbaneado",
            description=(
                f"**{user}** fue desbaneado."
            ),
            color=discord.Color.green()
        )
        embed.add_field(
            name="Usuario",
            value=(
                f"{user}\n"
                f"`{user.id}`"
            ),
            inline=False
        )
        await self.enviar_log(
            guild,
            embed
        )
    # ========================================================
    # ROL CREADO
    # ========================================================
    @commands.Cog.listener()
    async def on_guild_role_create(
        self,
        role
    ):
        embed = discord.Embed(
            title="🎨 Rol creado",
            description=(
                f"Se creó el rol {role.mention}."
            ),
            color=discord.Color.green()
        )
        embed.add_field(
            name="Nombre",
            value=f"`{role.name}`",
            inline=True
        )
        embed.add_field(
            name="ID",
            value=f"`{role.id}`",
            inline=True
        )
        await self.enviar_log(
            role.guild,
            embed
        )
    # ========================================================
    # ROL ELIMINADO
    # ========================================================
    @commands.Cog.listener()
    async def on_guild_role_delete(
        self,
        role
    ):
        embed = discord.Embed(
            title="🗑️ Rol eliminado",
            description=(
                f"Se eliminó el rol **{role.name}**."
            ),
            color=discord.Color.red()
        )
        embed.add_field(
            name="ID",
            value=f"`{role.id}`",
            inline=False
        )
        await self.enviar_log(
            role.guild,
            embed
        )
    # ========================================================
    # CANAL CREADO
    # ========================================================
    @commands.Cog.listener()
    async def on_guild_channel_create(
        self,
        channel
    ):
        if channel.guild is None:
            return
        embed = discord.Embed(
            title="📁 Canal creado",
            description=(
                f"Se creó {channel.mention}."
            ),
            color=discord.Color.green()
        )
        embed.add_field(
            name="Nombre",
            value=f"`{channel.name}`",
            inline=True
        )
        embed.add_field(
            name="Tipo",
            value=str(channel.type),
            inline=True
        )
        await self.enviar_log(
            channel.guild,
            embed
        )
    # ========================================================
    # CANAL ELIMINADO
    # ========================================================
    @commands.Cog.listener()
    async def on_guild_channel_delete(
        self,
        channel
    ):
        if channel.guild is None:
            return
        embed = discord.Embed(
            title="🗑️ Canal eliminado",
            description=(
                f"Se eliminó el canal **{channel.name}**."
            ),
            color=discord.Color.red()
        )
        embed.add_field(
            name="ID",
            value=f"`{channel.id}`",
            inline=False
        )
        await self.enviar_log(
            channel.guild,
            embed
        )
# ============================================================
# SETUP
# ============================================================
async def setup(bot):
    await bot.add_cog(
        Logs(bot)
    )