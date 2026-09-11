import discord
from discord import app_commands
from discord.ext import commands
class Bienvenida(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Cargar configuración automáticamente
        self.data = self.bot.load_cog_data("bienvenida")
    # ============================================================
    # GUARDAR CONFIGURACIÓN
    # ============================================================
    def save(self):
        self.bot.save_cog_data("bienvenida", self.data)
    # ============================================================
    # OBTENER CONFIGURACIÓN DEL SERVIDOR
    # ============================================================
    def get_config(self, guild_id: int):
        guild_id = str(guild_id)
        if guild_id not in self.data:
            self.data[guild_id] = {
                "welcome_channel": None,
                "rules_channel": None
            }
        return self.data[guild_id]
    # ============================================================
    # /CONFIGBIENVENIDA
    # ============================================================
    @app_commands.command(
        name="configbienvenida",
        description="Configura el canal donde se enviarán las bienvenidas."
    )
    @app_commands.describe(
        canal="Canal donde se enviarán las bienvenidas."
    )
    @app_commands.default_permissions(manage_guild=True)
    async def configbienvenida(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel
    ):
        config = self.get_config(interaction.guild.id)
        config["welcome_channel"] = canal.id
        self.save()
        embed = discord.Embed(
            title="💜 Bienvenida configurada",
            description=(
                f"Las bienvenidas se enviarán en {canal.mention}.\n\n"
                "También podés probar el sistema con `/testbienvenida`."
            ),
            color=discord.Color.from_rgb(115, 55, 210)
        )
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
    # ============================================================
    # /CONFIGREGLAS
    # ============================================================
    @app_commands.command(
        name="configreglas",
        description="Configura el canal que abrirá el botón de Reglas."
    )
    @app_commands.describe(
        canal="Canal de reglas que abrirá el botón."
    )
    @app_commands.default_permissions(manage_guild=True)
    async def configreglas(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel
    ):
        config = self.get_config(interaction.guild.id)
        config["rules_channel"] = canal.id
        self.save()
        embed = discord.Embed(
            title="📜 Reglas configuradas",
            description=(
                f"El botón **📜 Reglas** ahora abrirá {canal.mention}."
            ),
            color=discord.Color.from_rgb(115, 55, 210)
        )
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )
    # ============================================================
    # CREAR MENSAJE DE BIENVENIDA
    # ============================================================
    async def create_welcome_embed(
        self,
        member: discord.Member
    ):
        guild = member.guild
        # Número del miembro.
        # Discord no da un número exacto de ingreso histórico,
        # así que usamos la cantidad actual de miembros.
        member_count = guild.member_count or len(guild.members)
        embed = discord.Embed(
            title=f"👋 ¡Bienvenido/a a {guild.name}!",
            description=(
                f"¡Hola {member.mention}! 💜\n\n"
                "Nos alegra mucho tenerte acá.\n"
                "Esperamos que disfrutes tu estadía en el servidor.\n\n"
                f"**👥 Sos el miembro #{member_count}**"
            ),
            color=discord.Color.from_rgb(115, 55, 210)
        )
        # Avatar del usuario
        avatar_url = member.display_avatar.url
        embed.set_thumbnail(
            url=avatar_url
        )
        # Banner del servidor
        if guild.banner:
            embed.set_image(
                url=guild.banner.url
            )
        # Información inferior
        embed.set_footer(
            text=f"{guild.name} • ¡Disfrutá tu estadía!",
            icon_url=guild.icon.url if guild.icon else None
        )
        return embed
    # ============================================================
    # BOTÓN DE REGLAS
    # ============================================================
    def create_view(
        self,
        guild: discord.Guild
    ):
        config = self.get_config(guild.id)
        rules_channel_id = config.get("rules_channel")
        # Si no hay canal de reglas configurado,
        # no mostramos botones.
        if not rules_channel_id:
            return None
        rules_channel = guild.get_channel(
            rules_channel_id
        )
        if not rules_channel:
            return None
        view = discord.ui.View(
            timeout=None
        )
        button = discord.ui.Button(
            label="Reglas",
            emoji="📜",
            style=discord.ButtonStyle.secondary,
            url=rules_channel.jump_url
        )
        view.add_item(button)
        return view
    # ============================================================
    # TEST DE BIENVENIDA
    # ============================================================
    @app_commands.command(
        name="testbienvenida",
        description="Envía una prueba del mensaje de bienvenida."
    )
    @app_commands.default_permissions(manage_guild=True)
    async def testbienvenida(
        self,
        interaction: discord.Interaction
    ):
        config = self.get_config(interaction.guild.id)
        channel_id = config.get("welcome_channel")
        if not channel_id:
            await interaction.response.send_message(
                "❌ Primero configurá el canal con `/configbienvenida`.",
                ephemeral=True
            )
            return
        channel = interaction.guild.get_channel(
            channel_id
        )
        if not channel:
            await interaction.response.send_message(
                "❌ El canal configurado ya no existe.",
                ephemeral=True
            )
            return
        embed = await self.create_welcome_embed(
            interaction.user
        )
        view = self.create_view(
            interaction.guild
        )
        try:
            await channel.send(
                embed=embed,
                view=view
            )
            await interaction.response.send_message(
                f"✅ Mensaje de prueba enviado en {channel.mention}.",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ No tengo permisos para enviar mensajes en ese canal.",
                ephemeral=True
            )
        except Exception as e:
            print(
                f"[BIENVENIDA] Error en test: {e}"
            )
            await interaction.response.send_message(
                "❌ Ocurrió un error al enviar la prueba.",
                ephemeral=True
            )
    # ============================================================
    # CUANDO ENTRA UN MIEMBRO
    # ============================================================
    @commands.Cog.listener()
    async def on_member_join(
        self,
        member: discord.Member
    ):
        config = self.get_config(member.guild.id)
        channel_id = config.get("welcome_channel")
        if not channel_id:
            return
        channel = member.guild.get_channel(
            channel_id
        )
        if not channel:
            return
        embed = await self.create_welcome_embed(
            member
        )
        view = self.create_view(
            member.guild
        )
        try:
            await channel.send(
                content=member.mention,
                embed=embed,
                view=view
            )
            print(
                f"[BIENVENIDA] {member} entró a {member.guild.name}"
            )
        except discord.Forbidden:
            print(
                f"[BIENVENIDA] Sin permisos para enviar mensajes en #{channel.name}"
            )
        except Exception as e:
            print(
                f"[BIENVENIDA] Error: {e}"
            )
async def setup(bot):
    await bot.add_cog(
        Bienvenida(bot)
    )

Cómo se usa

Primero:

/configbienvenida #bienvenidas

Después:

/configreglas #reglas

Y para probarlo:

/testbienvenida

Cuando entre alguien nuevo, automáticamente aparecerá su avatar, el banner del servidor, el contador de miembros y el botón 📜 Reglas.

Importante: el bot necesita tener Ver canal, Enviar mensajes, Insertar enlaces y Usar enlaces en el canal de bienvenida.