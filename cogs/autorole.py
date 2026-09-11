import json
import os
import re

import discord
from discord import app_commands
from discord.ext import commands


# ============================================================
# ARCHIVOS
# ============================================================

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "autoroles.json")


# ============================================================
# UTILIDADES
# ============================================================

def ensure_data():

    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(DATA_FILE):

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4, ensure_ascii=False)


def load_data():

    ensure_data()

    try:

        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:

        return {}


def save_data(data):

    ensure_data()

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def get_guild_config(guild_id):

    data = load_data()

    guild_id = str(guild_id)

    if guild_id not in data:

        data[guild_id] = {
            "allowed_role_id": None,
            "created_roles": {}
        }

        save_data(data)

    return data[guild_id]


def hex_to_colour(value):

    value = value.replace("#", "").strip()

    if not re.fullmatch(r"[0-9a-fA-F]{6}", value):
        return None

    return discord.Colour(int(value, 16))


# ============================================================
# COG
# ============================================================

class AutoRole(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        ensure_data()

    # ========================================================
    # COMPROBAR PERMISO
    # ========================================================

    async def check_creator_permission(self, interaction):

        if not interaction.guild:
            return False

        # Administradores siempre pueden usarlo
        if interaction.user.guild_permissions.administrator:
            return True

        config = get_guild_config(interaction.guild.id)

        allowed_role_id = config.get("allowed_role_id")

        if not allowed_role_id:
            return False

        role = interaction.guild.get_role(
            int(allowed_role_id)
        )

        if not role:
            return False

        return role in interaction.user.roles

    # ========================================================
    # /CONFIGURAR
    # ========================================================

    @app_commands.command(
        name="configurar",
        description="Configura qué rol puede crear roles personalizados."
    )
    @app_commands.describe(
        rol="El rol que podrá utilizar el sistema."
    )
    @app_commands.default_permissions(administrator=True)
    async def configurar(
        self,
        interaction: discord.Interaction,
        rol: discord.Role
    ):

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Necesitás ser administrador para configurar esto.",
                ephemeral=True
            )

            return

        # El bot debe poder administrar el rol
        if rol >= interaction.guild.me.top_role:

            await interaction.response.send_message(
                "❌ No puedo utilizar ese rol porque está por encima "
                "o al mismo nivel que mi rol más alto.",
                ephemeral=True
            )

            return

        data = load_data()

        guild_id = str(interaction.guild.id)

        if guild_id not in data:

            data[guild_id] = {
                "allowed_role_id": None,
                "created_roles": {}
            }

        data[guild_id]["allowed_role_id"] = rol.id

        save_data(data)

        embed = discord.Embed(
            title="⚙️ Configuración actualizada",
            description=(
                f"Ahora los miembros que tengan {rol.mention} "
                "podrán crear y administrar sus roles personalizados."
            ),
            colour=discord.Colour.from_rgb(115, 55, 210)
        )

        embed.add_field(
            name="Rol permitido",
            value=rol.mention,
            inline=False
        )

        embed.set_footer(
            text="Auto Role System"
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ========================================================
    # /CREARROL
    # ========================================================

    @app_commands.command(
        name="crearrol",
        description="Crea tu propio rol personalizado."
    )
    @app_commands.describe(
        nombre="Nombre del nuevo rol.",
        color="Color HEX. Ejemplo: #8B5CF6",
        icono="Emoji personalizado del servidor que será el ícono del rol."
    )
    async def crearrol(
        self,
        interaction: discord.Interaction,
        nombre: str,
        color: str,
        icono: discord.Emoji = None
    ):

        allowed = await self.check_creator_permission(interaction)

        if not allowed:

            config = get_guild_config(
                interaction.guild.id
            )

            role_id = config.get("allowed_role_id")

            if role_id:

                role = interaction.guild.get_role(
                    int(role_id)
                )

                role_text = role.mention if role else "el rol configurado"

            else:

                role_text = "el rol configurado"

            await interaction.response.send_message(
                f"❌ No podés utilizar este comando.\n\n"
                f"Necesitás tener {role_text}.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # VALIDACIONES
        # ----------------------------------------------------

        nombre = nombre.strip()

        if len(nombre) < 1 or len(nombre) > 100:

            await interaction.response.send_message(
                "❌ El nombre debe tener entre 1 y 100 caracteres.",
                ephemeral=True
            )

            return

        colour = hex_to_colour(color)

        if colour is None:

            await interaction.response.send_message(
                "❌ Color inválido.\n"
                "Usá un formato como `#8B5CF6`.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # LÍMITE
        # ----------------------------------------------------

        data = load_data()

        guild_id = str(interaction.guild.id)

        if guild_id not in data:

            data[guild_id] = {
                "allowed_role_id": None,
                "created_roles": {}
            }

        created_roles = data[guild_id].setdefault(
            "created_roles",
            {}
        )

        user_id = str(interaction.user.id)

        # Si ya tiene uno, eliminarlo antes
        if user_id in created_roles:

            old_role_id = created_roles[user_id].get(
                "role_id"
            )

            old_role = interaction.guild.get_role(
                int(old_role_id)
            ) if old_role_id else None

            if old_role:

                try:
                    await old_role.delete(
                        reason="Reemplazo de rol personalizado"
                    )
                except discord.Forbidden:

                    await interaction.response.send_message(
                        "❌ No puedo eliminar tu rol anterior. "
                        "Revisá la posición de mi rol.",
                        ephemeral=True
                    )

                    return

        # ----------------------------------------------------
        # CREAR ROL
        # ----------------------------------------------------

        try:

            role = await interaction.guild.create_role(
                name=nombre,
                colour=colour,
                reason=f"Rol personalizado de {interaction.user}"
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ No tengo permiso para crear roles.",
                ephemeral=True
            )

            return

        except discord.HTTPException as e:

            await interaction.response.send_message(
                f"❌ Discord rechazó la creación del rol.\n"
                f"`{e}`",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # ÍCONO DEL ROL
        # ----------------------------------------------------

        icon_success = False

        if icono:

            try:

                await role.edit(
                    display_icon=icono
                )

                icon_success = True

            except discord.Forbidden:
                pass

            except discord.HTTPException:
                pass

        # ----------------------------------------------------
        # DAR ROL
        # ----------------------------------------------------

        try:

            await interaction.user.add_roles(
                role,
                reason="Rol personalizado"
            )

        except discord.Forbidden:

            try:
                await role.delete()
            except:
                pass

            await interaction.response.send_message(
                "❌ No puedo darte el rol. "
                "Revisá que mi rol esté por encima del rol creado.",
                ephemeral=True
            )

            return

        # ----------------------------------------------------
        # GUARDAR
        # ----------------------------------------------------

        created_roles[user_id] = {
            "role_id": role.id,
            "owner_id": interaction.user.id,
            "icon": str(icono) if icono else None
        }

        save_data(data)

        # ----------------------------------------------------
        # RESPUESTA
        # ----------------------------------------------------

        embed = discord.Embed(
            title="🎨 Rol personalizado creado",
            description=(
                f"{interaction.user.mention}, tu rol fue creado correctamente."
            ),
            colour=colour
        )

        embed.add_field(
            name="Rol",
            value=role.mention,
            inline=True
        )

        embed.add_field(
            name="Color",
            value=color.upper(),
            inline=True
        )

        if icono:

            icon_status = (
                "✅ Ícono aplicado"
                if icon_success
                else
                "⚠️ No se pudo aplicar el ícono"
            )

            embed.add_field(
                name="Ícono",
                value=f"{icono} — {icon_status}",
                inline=False
            )

        embed.add_field(
            name="Compartir",
            value=(
                "`/compartirrol @usuario`"
            ),
            inline=False
        )

        embed.set_footer(
            text="Auto Role System"
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ========================================================
    # /COMPARTIRROL
    # ========================================================

    @app_commands.command(
        name="compartirrol",
        description="Comparte tu rol personalizado con otro miembro."
    )
    @app_commands.describe(
        usuario="Usuario que recibirá tu rol."
    )
    async def compartirrol(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member
    ):

        data = load_data()

        guild_id = str(interaction.guild.id)

        guild_data = data.get(guild_id, {})

        created_roles = guild_data.get(
            "created_roles",
            {}
        )

        owner_data = created_roles.get(
            str(interaction.user.id)
        )

        if not owner_data:

            await interaction.response.send_message(
                "❌ No tenés un rol personalizado.",
                ephemeral=True
            )

            return

        role_id = owner_data.get("role_id")

        role = interaction.guild.get_role(
            int(role_id)
        ) if role_id else None

        if not role:

            await interaction.response.send_message(
                "❌ Tu rol personalizado ya no existe.",
                ephemeral=True
            )

            return

        # No permitir compartir con bots
        if usuario.bot:

            await interaction.response.send_message(
                "❌ No podés compartir el rol con un bot.",
                ephemeral=True
            )

            return

        # Comprobar jerarquía
        if role >= interaction.guild.me.top_role:

            await interaction.response.send_message(
                "❌ No puedo administrar ese rol porque mi rol "
                "está por debajo.",
                ephemeral=True
            )

            return

        try:

            await usuario.add_roles(
                role,
                reason=f"Rol compartido por {interaction.user}"
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "❌ No puedo darle ese rol al usuario.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title="🔗 Rol compartido",
            description=(
                f"{interaction.user.mention} compartió "
                f"{role.mention} con {usuario.mention}."
            ),
            colour=role.colour
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ========================================================
    # /ELIMINARROL
    # ========================================================

    @app_commands.command(
        name="eliminarrol",
        description="Elimina tu rol personalizado."
    )
    async def eliminarrol(
        self,
        interaction: discord.Interaction
    ):

        data = load_data()

        guild_id = str(interaction.guild.id)

        guild_data = data.get(guild_id, {})

        created_roles = guild_data.get(
            "created_roles",
            {}
        )

        user_id = str(interaction.user.id)

        owner_data = created_roles.get(user_id)

        if not owner_data:

            await interaction.response.send_message(
                "❌ No tenés un rol personalizado.",
                ephemeral=True
            )

            return

        role_id = owner_data.get("role_id")

        role = interaction.guild.get_role(
            int(role_id)
        ) if role_id else None

        if role:

            try:
                await role.delete(
                    reason="Eliminación de rol personalizado"
                )
            except discord.Forbidden:

                await interaction.response.send_message(
                    "❌ No puedo eliminar tu rol.",
                    ephemeral=True
                )

                return

        del created_roles[user_id]

        save_data(data)

        await interaction.response.send_message(
            "✅ Tu rol personalizado fue eliminado.",
            ephemeral=True
        )

    # ========================================================
    # /MIROL
    # ========================================================

    @app_commands.command(
        name="mirol",
        description="Muestra información sobre tu rol personalizado."
    )
    async def mirol(
        self,
        interaction: discord.Interaction
    ):

        data = load_data()

        guild_data = data.get(
            str(interaction.guild.id),
            {}
        )

        created_roles = guild_data.get(
            "created_roles",
            {}
        )

        owner_data = created_roles.get(
            str(interaction.user.id)
        )

        if not owner_data:

            await interaction.response.send_message(
                "❌ No tenés un rol personalizado.",
                ephemeral=True
            )

            return

        role = interaction.guild.get_role(
            int(owner_data["role_id"])
        )

        if not role:

            await interaction.response.send_message(
                "❌ Tu rol ya no existe.",
                ephemeral=True
            )

            return

        embed = discord.Embed(
            title="🎨 Tu rol personalizado",
            colour=role.colour
        )

        embed.add_field(
            name="Nombre",
            value=role.name,
            inline=True
        )

        embed.add_field(
            name="ID",
            value=str(role.id),
            inline=True
        )

        embed.add_field(
            name="Color",
            value=f"`#{role.colour.value:06X}`",
            inline=True
        )

        embed.add_field(
            name="Miembros",
            value=str(len(role.members)),
            inline=True
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    # ========================================================
    # /CONFIGURACION
    # ========================================================

    @app_commands.command(
        name="configuracion",
        description="Muestra la configuración del sistema."
    )
    @app_commands.default_permissions(administrator=True)
    async def configuracion(
        self,
        interaction: discord.Interaction
    ):

        if not interaction.user.guild_permissions.administrator:

            await interaction.response.send_message(
                "❌ Necesitás ser administrador.",
                ephemeral=True
            )

            return

        config = get_guild_config(
            interaction.guild.id
        )

        role_id = config.get(
            "allowed_role_id"
        )

        role = (
            interaction.guild.get_role(int(role_id))
            if role_id
            else None
        )

        created = len(
            config.get("created_roles", {})
        )

        embed = discord.Embed(
            title="⚙️ Configuración",
            colour=discord.Colour.from_rgb(
                115,
                55,
                210
            )
        )

        embed.add_field(
            name="Rol autorizado",
            value=role.mention if role else "No configurado",
            inline=False
        )

        embed.add_field(
            name="Roles personalizados",
            value=str(created),
            inline=False
        )

        embed.set_footer(
            text="Auto Role System"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):

    await bot.add_cog(
        AutoRole(bot)
    )