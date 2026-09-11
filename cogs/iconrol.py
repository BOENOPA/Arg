import os
import json
import re
import discord
from discord import app_commands
from discord.ext import commands
# ============================================================
# CONFIGURACIÓN
# ============================================================
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "autoroles.json")
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
    except (json.JSONDecodeError, OSError):
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
            "allowed_role": None,
            "custom_roles": {}
        }
    if "custom_roles" not in data[guild_id]:
        data[guild_id]["custom_roles"] = {}
    return data[guild_id]
def parse_hex_color(color):
    color = color.strip().replace("#", "")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", color):
        return None
    try:
        return discord.Color(int(color, 16))
    except ValueError:
        return None
def parse_custom_emoji(emoji_text):
    """
    Acepta:
    <:nombre:123456789>
    <a:nombre:123456789>
    """
    if not emoji_text:
        return None
    pattern = r"<(a?):([a-zA-Z0-9_]+):(\d+)>"
    match = re.fullmatch(pattern, emoji_text.strip())
    if not match:
        return None
    animated = bool(match.group(1))
    emoji_id = int(match.group(3))
    return {
        "id": emoji_id,
        "animated": animated
    }
def encontrar_emoji(guild, emoji_id):
    return discord.utils.get(
        guild.emojis,
        id=emoji_id
    )
def tiene_permiso_configuracion(member):
    return (
        member.guild_permissions.administrator
        or member.guild_permissions.manage_guild
    )
# ============================================================
# COG
# ============================================================
class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = cargar_datos()
    # ========================================================
    # CONFIGURAR
    # ========================================================
    @app_commands.command(
        name="configurar",
        description="Configura qué rol puede crear roles personalizados."
    )
    @app_commands.describe(
        rol="Rol que podrán usar para crear roles personalizados."
    )
    async def configurar(
        self,
        interaction: discord.Interaction,
        rol: discord.Role
    ):
        if not tiene_permiso_configuracion(
            interaction.user
        ):
            await interaction.response.send_message(
                "❌ Necesitás tener **Administrador** o "
                "**Gestionar servidor** para configurar esto.",
                ephemeral=True
            )
            return
        guild_data = get_guild_data(
            self.data,
            interaction.guild.id
        )
        guild_data["allowed_role"] = rol.id
        guardar_datos(self.data)
        embed = discord.Embed(
            title="⚙️ Configuración actualizada",
            description=(
                f"Ahora los miembros con {rol.mention} "
                "podrán crear roles personalizados."
            ),
            color=discord.Color.purple()
        )
        embed.set_footer(
            text="Auto Role System"
        )
        await interaction.response.send_message(
            embed=embed
        )
    # ========================================================
    # CREAR ROL
    # ========================================================
    @app_commands.command(
        name="crearrol",
        description="Crea tu propio rol personalizado."
    )
    @app_commands.describe(
        nombre="Nombre del nuevo rol.",
        color="Color HEX. Ejemplo: #8A2BE2",
        emoji="Emoji personalizado del servidor. Ejemplo: <:corazon:123456789>"
    )
    async def crearrol(
        self,
        interaction: discord.Interaction,
        nombre: str,
        color: str,
        emoji: str = None
    ):
        member = interaction.user
        guild = interaction.guild
        guild_data = get_guild_data(
            self.data,
            guild.id
        )
        # ----------------------------------------------------
        # COMPROBAR ROL PERMITIDO
        # ----------------------------------------------------
        allowed_role_id = guild_data.get(
            "allowed_role"
        )
        if not allowed_role_id:
            await interaction.response.send_message(
                "❌ El sistema todavía no está configurado.\n\n"
                "Un administrador debe utilizar `/configurar`.",
                ephemeral=True
            )
            return
        allowed_role = guild.get_role(
            allowed_role_id
        )
        if allowed_role is None:
            await interaction.response.send_message(
                "❌ El rol configurado ya no existe.",
                ephemeral=True
            )
            return
        if (
            not member.guild_permissions.administrator
            and allowed_role not in member.roles
        ):
            await interaction.response.send_message(
                "❌ No tenés permiso para crear roles personalizados.",
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # COMPROBAR SI YA TIENE ROL
        # ----------------------------------------------------
        user_id = str(member.id)
        existing = guild_data["custom_roles"].get(
            user_id
        )
        if existing:
            existing_role = guild.get_role(
                existing.get("role_id")
            )
            if existing_role:
                await interaction.response.send_message(
                    "❌ Ya tenés un rol personalizado.\n\n"
                    f"Tu rol actual es {existing_role.mention}.\n"
                    "Eliminalo con `/eliminarrol` para crear otro.",
                    ephemeral=True
                )
                return
            else:
                del guild_data["custom_roles"][user_id]
                guardar_datos(self.data)
        # ----------------------------------------------------
        # VALIDAR NOMBRE
        # ----------------------------------------------------
        nombre = nombre.strip()
        if not nombre:
            await interaction.response.send_message(
                "❌ El nombre no puede estar vacío.",
                ephemeral=True
            )
            return
        if len(nombre) > 100:
            await interaction.response.send_message(
                "❌ El nombre no puede superar los **100 caracteres**.",
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # VALIDAR COLOR
        # ----------------------------------------------------
        discord_color = parse_hex_color(
            color
        )
        if discord_color is None:
            await interaction.response.send_message(
                "❌ Color inválido.\n\n"
                "Usá un color HEX de 6 caracteres.\n"
                "Ejemplo: `#8A2BE2`",
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # VALIDAR EMOJI
        # ----------------------------------------------------
        emoji_data = None
        emoji_object = None
        if emoji:
            emoji_data = parse_custom_emoji(
                emoji
            )
            if emoji_data is None:
                await interaction.response.send_message(
                    "❌ Emoji inválido.\n\n"
                    "Tenés que usar un emoji personalizado "
                    "del servidor.\n\n"
                    "Ejemplo:\n"
                    "`<:corazon:123456789>`",
                    ephemeral=True
                )
                return
            emoji_object = encontrar_emoji(
                guild,
                emoji_data["id"]
            )
            if emoji_object is None:
                await interaction.response.send_message(
                    "❌ Ese emoji no pertenece a este servidor.",
                    ephemeral=True
                )
                return
        # ----------------------------------------------------
        # COMPROBAR JERARQUÍA DEL BOT
        # ----------------------------------------------------
        bot_member = guild.me
        if bot_member is None:
            await interaction.response.send_message(
                "❌ No pude encontrar al bot dentro del servidor.",
                ephemeral=True
            )
            return
        if not bot_member.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "❌ No tengo permiso para **Gestionar roles**.",
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # CREAR ROL
        # ----------------------------------------------------
        try:
            role = await guild.create_role(
                name=nombre,
                colour=discord_color,
                reason=f"Rol personalizado creado por {member}"
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Discord rechazó la creación del rol.\n\n"
                "Asegurate de que el bot tenga **Gestionar roles**.",
                ephemeral=True
            )
            return
        except discord.HTTPException as e:
            await interaction.response.send_message(
                f"❌ Discord devolvió un error al crear el rol.\n"
                f"`{e}`",
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # ICONO DEL ROL
        # ----------------------------------------------------
        icon_success = False
        if emoji_object:
            try:
                # Descargar bytes del emoji
                emoji_bytes = await emoji_object.read()
                await role.edit(
                    display_icon=emoji_bytes,
                    reason="Icono de rol personalizado"
                )
                icon_success = True
            except discord.Forbidden:
                icon_success = False
            except discord.HTTPException:
                icon_success = False
            except Exception:
                icon_success = False
        # ----------------------------------------------------
        # DAR ROL AL USUARIO
        # ----------------------------------------------------
        try:
            await member.add_roles(
                role,
                reason="Rol personalizado"
            )
        except discord.Forbidden:
            try:
                await role.delete(
                    reason="No se pudo asignar el rol"
                )
            except Exception:
                pass
            await interaction.response.send_message(
                "❌ Creé el rol, pero no pude asignártelo.\n\n"
                "Verificá la posición del rol del bot.",
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # GUARDAR DATOS
        # ----------------------------------------------------
        guild_data["custom_roles"][user_id] = {
            "role_id": role.id,
            "role_name": role.name,
            "color": color.replace("#", "").upper(),
            "emoji_id": (
                emoji_object.id
                if emoji_object
                else None
            ),
            "owner_id": member.id
        }
        guardar_datos(self.data)
        # ----------------------------------------------------
        # RESPUESTA
        # ----------------------------------------------------
        embed = discord.Embed(
            title="🎨 Rol personalizado creado",
            color=discord_color
        )
        embed.description = (
            f"Tu rol {role.mention} fue creado correctamente.\n\n"
            f"**Nombre:** `{role.name}`\n"
            f"**Color:** `#{color.replace('#', '').upper()}`"
        )
        if emoji_object:
            if icon_success:
                embed.add_field(
                    name="Icono",
                    value=f"{emoji_object} personalizado",
                    inline=False
                )
            else:
                embed.add_field(
                    name="Icono",
                    value=(
                        "⚠️ El emoji fue detectado, "
                        "pero Discord no permitió colocarlo como icono."
                    ),
                    inline=False
                )
        embed.add_field(
            name="Compartir",
            value=(
                "Usá `/compartirrol @usuario` "
                "para darle tu rol a otra persona."
            ),
            inline=False
        )
        embed.set_footer(
            text=f"Creado por {member}"
        )
        await interaction.response.send_message(
            embed=embed
        )
    # ========================================================
    # COMPARTIR ROL
    # ========================================================
    @app_commands.command(
        name="compartirrol",
        description="Comparte tu rol personalizado con otro miembro."
    )
    @app_commands.describe(
        miembro="Miembro que recibirá tu rol."
    )
    async def compartirrol(
        self,
        interaction: discord.Interaction,
        miembro: discord.Member
    ):
        member = interaction.user
        guild = interaction.guild
        guild_data = get_guild_data(
            self.data,
            guild.id
        )
        user_id = str(member.id)
        custom_role = guild_data[
            "custom_roles"
        ].get(user_id)
        if not custom_role:
            await interaction.response.send_message(
                "❌ No tenés un rol personalizado.",
                ephemeral=True
            )
            return
        role = guild.get_role(
            custom_role.get("role_id")
        )
        if role is None:
            await interaction.response.send_message(
                "❌ Tu rol personalizado ya no existe.",
                ephemeral=True
            )
            return
        if miembro.bot:
            await interaction.response.send_message(
                "❌ No podés compartir tu rol con un bot.",
                ephemeral=True
            )
            return
        # ----------------------------------------------------
        # JERARQUÍA
        # ----------------------------------------------------
        if role >= guild.me.top_role:
            await interaction.response.send_message(
                "❌ El rol está demasiado alto para que pueda "
                "administrarlo.",
                ephemeral=True
            )
            return
        try:
            await miembro.add_roles(
                role,
                reason=f"Rol compartido por {member}"
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ No pude darle el rol a ese miembro.\n\n"
                "Probablemente el rol está por encima del "
                "rol más alto del bot.",
                ephemeral=True
            )
            return
        except discord.HTTPException:
            await interaction.response.send_message(
                "❌ Discord rechazó la operación.",
                ephemeral=True
            )
            return
        embed = discord.Embed(
            title="🤝 Rol compartido",
            description=(
                f"Le diste tu rol {role.mention} a "
                f"{miembro.mention}."
            ),
            color=role.color
        )
        await interaction.response.send_message(
            embed=embed
        )
    # ========================================================
    # ELIMINAR ROL
    # ========================================================
    @app_commands.command(
        name="eliminarrol",
        description="Elimina tu rol personalizado."
    )
    async def eliminarrol(
        self,
        interaction: discord.Interaction
    ):
        member = interaction.user
        guild = interaction.guild
        guild_data = get_guild_data(
            self.data,
            guild.id
        )
        user_id = str(member.id)
        custom_role = guild_data[
            "custom_roles"
        ].get(user_id)
        if not custom_role:
            await interaction.response.send_message(
                "❌ No tenés un rol personalizado.",
                ephemeral=True
            )
            return
        role = guild.get_role(
            custom_role.get("role_id")
        )
        del guild_data[
            "custom_roles"
        ][user_id]
        guardar_datos(self.data)
        if role:
            try:
                await role.delete(
                    reason=f"Rol eliminado por {member}"
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "⚠️ Eliminé el registro, pero no pude "
                    "eliminar el rol de Discord.",
                    ephemeral=True
                )
                return
            except discord.HTTPException:
                await interaction.response.send_message(
                    "⚠️ Eliminé el registro, pero Discord "
                    "no permitió eliminar el rol.",
                    ephemeral=True
                )
                return
        await interaction.response.send_message(
            "🗑️ Tu rol personalizado fue eliminado."
        )
    # ========================================================
    # MI ROL
    # ========================================================
    @app_commands.command(
        name="mirol",
        description="Muestra información sobre tu rol personalizado."
    )
    async def mirol(
        self,
        interaction: discord.Interaction
    ):
        member = interaction.user
        guild = interaction.guild
        guild_data = get_guild_data(
            self.data,
            guild.id
        )
        custom_role = guild_data[
            "custom_roles"
        ].get(str(member.id))
        if not custom_role:
            await interaction.response.send_message(
                "❌ No tenés un rol personalizado.",
                ephemeral=True
            )
            return
        role = guild.get_role(
            custom_role.get("role_id")
        )
        if role is None:
            await interaction.response.send_message(
                "❌ Tu rol personalizado ya no existe.",
                ephemeral=True
            )
            return
        embed = discord.Embed(
            title="🎨 Tu rol personalizado",
            color=role.color
        )
        embed.add_field(
            name="Rol",
            value=role.mention,
            inline=False
        )
        embed.add_field(
            name="Nombre",
            value=f"`{role.name}`",
            inline=True
        )
        embed.add_field(
            name="Color",
            value=f"`#{role.color.value:06X}`",
            inline=True
        )
        embed.add_field(
            name="ID",
            value=f"`{role.id}`",
            inline=False
        )
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
    # ========================================================
    # CONFIGURACIÓN
    # ========================================================
    @app_commands.command(
        name="configuracion",
        description="Muestra la configuración del sistema."
    )
    async def configuracion(
        self,
        interaction: discord.Interaction
    ):
        if not tiene_permiso_configuracion(
            interaction.user
        ):
            await interaction.response.send_message(
                "❌ Necesitás permisos de administrador "
                "o gestionar servidor.",
                ephemeral=True
            )
            return
        guild_data = get_guild_data(
            self.data,
            interaction.guild.id
        )
        role_id = guild_data.get(
            "allowed_role"
        )
        role = (
            interaction.guild.get_role(role_id)
            if role_id
            else None
        )
        custom_roles = guild_data.get(
            "custom_roles",
            {}
        )
        embed = discord.Embed(
            title="⚙️ Configuración — Auto Role",
            color=discord.Color.purple()
        )
        embed.add_field(
            name="Rol autorizado",
            value=(
                role.mention
                if role
                else "❌ No configurado"
            ),
            inline=False
        )
        embed.add_field(
            name="Roles personalizados",
            value=str(len(custom_roles)),
            inline=True
        )
        embed.set_footer(
            text="Auto Role System"
        )
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
# ============================================================
# SETUP
# ============================================================
async def setup(bot):
    await bot.add_cog(
        AutoRole(bot)
    )