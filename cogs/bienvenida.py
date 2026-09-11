import discord
from discord import app_commands
from discord.ext import commands
class Bienvenida(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = self.bot.load_cog_data("bienvenida")
    # ============================================================
    # DATOS
    # ============================================================
    def save(self):
        self.bot.save_cog_data("bienvenida", self.data)
    def get_config(self, guild_id: int):
        guild_id = str(guild_id)
        if guild_id not in self.data:
            self.data[guild_id] = {
                "welcome_channel": None,
                "rules_channel": None
            }
            self.save()
        return self.data[guild_id]
    # ============================================================
    # COMPROBAR PERMISOS
    # ============================================================
    async def check_admin(
        self,
        interaction: discord.Interaction
    ) -> bool:
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
                "❌ Necesitás el permiso **Gestionar servidor** para utilizar este comando.",
                ephemeral=True
            )
            return False
        return True
    # ============================================================
    # /CONFIGBIENVENIDA
    # ============================================================
    @app_commands.command(
        name="configbienvenida",
        description="Configura el canal de bienvenida."
    )
    @app_commands.describe(
        canal="Canal donde se enviarán las bienvenidas."
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def configbienvenida(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel
    ):
        if not await self.check_admin(interaction):
            return
        config = self.get_config(interaction.guild.id)
        config["welcome_channel"] = canal.id
        self.save()
        embed = discord.Embed(
            title="💜 Bienvenida configurada",
            description=(
                f"Las bienvenidas se enviarán en {canal.mention}.\n\n"
                "Podés utilizar `/testbienvenida` para probar el sistema."
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
        description="Configura el canal que abrirá el botón Reglas."
    )
    @app_commands.describe(
        canal="Canal que abrirá el botón de reglas."
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def configreglas(
        self,
        interaction: discord.Interaction,
        canal: discord.TextChannel
    ):
        if not await self.check_admin(interaction):
            return
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
    # CREAR EMBED
    # ============================================================
    async def create_welcome_embed(
        self,
        member: discord.Member
    ):
        guild = member.guild
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
        embed.set_thumbnail(
            url=member.display_avatar.url
        )
        # Banner del servidor
        if guild.banner:
            embed.set_image(
                url=guild.banner.url
            )
        # Footer
        embed.set_footer(
            text=f"{guild.name} • ¡Disfrutá tu estadía!",
            icon_url=guild.icon.url if guild.icon else None
        )
        return embed
    # ============================================================
    # BOTÓN REGLAS
    # ============================================================
    def create_view(
        self,
        guild: discord.Guild
    ):
        config = self.get_config(guild.id)
        rules_channel_id = config.get("rules_channel")
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
    # /TESTBIENVENIDA
    # ============================================================
    @app_commands.command(
        name="testbienvenida",
        description="Prueba el mensaje de bienvenida."
    )
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def testbienvenida(
        self,
        interaction: discord.Interaction
    ):
        if not await self.check_admin(interaction):
            return
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
                content=interaction.user.mention,
                embed=embed,
                view=view
            )
            await interaction.response.send_message(
                f"✅ Prueba enviada correctamente en {channel.mention}.",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ No tengo permisos suficientes en ese canal.",
                ephemeral=True
            )
        except Exception as e:
            print(f"[BIENVENIDA] Error en test: {e}")
            await interaction.response.send_message(
                "❌ Ocurrió un error al enviar la prueba.",
                ephemeral=True
            )
    # ============================================================
    # NUEVO MIEMBRO
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
                f"[BIENVENIDA] Sin permisos para enviar "
                f"mensajes en #{channel.name}"
            )
        except Exception as e:
            print(
                f"[BIENVENIDA] Error: {e}"
            )
# ================================================================
# CARGAR COG
# ================================================================
async def setup(bot):
    await bot.add_cog(
        Bienvenida(bot)
    )