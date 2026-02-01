from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional, List, Set, Tuple

import discord
from discord.ui import Button, View

from src.utils import get_logger

logger = get_logger(__name__)

# =============================================================
# contribute — polished embeds + simple ui
# goals:
# - reads like product microcopy (not "motivational quotes")
# - all lowercase
# - straight apostrophes only
# - no emojis in footers
# - minimal emoji usage, only where it adds clarity
# =============================================================

# =============================================================
# custom emojis (server emojis)
# =============================================================

E: Dict[str, str] = {
    "winner": "<:winner:1443290849806123160>",
    "trendmakers": "<:trendmakers:1449806723903918150>",
    "traders": "<:traders:1449806237163327669>",
    "tide": "<:tide:1449806235099598960>",
    "staff": "<:staff:1438608794648187082>",
    "speculator": "<:speculator:1449806233849692253>",
    "sketch": "<:sketch:1449806228501823500>",
    "sculptor": "<:sculptor:1449806226857787542>",
    "parliament": "<:parliament:1448017038781055130>",
    "orator": "<:orator:1449806221195350240>",
    "moderator": "<:moderator:1438572280157442108>",
    "lead": "<:lead:1449806230272086119>",
    "ink": "<:ink:1449806222600573000>",
    "friends": "<:friends:1438572518653820948>",
    "frame": "<:frame:1449806219437932713>",
    "foundingdroplet": "<:foundingdroplet:1438572470130049034>",
    "educators": "<:educators:1448016933545971753>",
    "droplet": "<:droplet:1438572493043404820>",
    "drip": "<:drip:1449806218137960630>",
    "degen": "<:degen:1449806231861461113>",
    "content": "<:content:1448017142380495031>",
    "bigdrop": "<:bigdrop:1438572306107600978>",
    "artists": "<:artists:1449806866589941841>",
    "allin": "<:allin:1438572205444431914>",
    "automata": "<:automata:1438572253586657311>",
    "helper": "<:helper:1455530669924155519>",
    "join": "<:join:1456391461045141616>",
    "portfolio": "<:portfolio:1456391514602213478>",
}

PE: Dict[str, discord.PartialEmoji] = {
    k: discord.PartialEmoji(name=k, id=int(v.split(":")[-1].replace(">", "")))
    for k, v in E.items()
}

# =============================================================
# palette
# =============================================================

LIQUID = 0x83C2EB
LIQUID_SOFT = 0x83C2EB
GOLD_SOFT = 0xE6D17A
PINK_SOFT = 0xFF6B6B
PURPLE_SOFT = 0x9B59B6
DESIGN_PINK = 0xE91E63

MAX_GUILDS = 2

HERO_IMAGE_URL = "https://media.discordapp.net/attachments/1441453165940707428/1455276406320926924/roles-4.png?ex=69542344&is=6952d1c4&hm=20f40c792662539e9f3a8f17d87f2c07df83c401e5d0ac0414a0e15d183d78e5&=&format=webp&quality=lossless&width=3360&height=1522"
SPECIAL_ROLES_IMAGE_URL = "https://imgur.com/dTJAnjO.png"
CHOOSE_GUILD_IMAGE_URL = "https://i.imgur.com/de1wcPm.png"
GUILD_PATHS_IMAGE_URL = "https://i.imgur.com/oDHpDsy.png"
ROLES_IMAGE_URL = "https://imgur.com/CKvaPiK.png"
PORTFOLIO_IMAGE_URL = "https://i.imgur.com/998HBnV.png"
DESIGNERS_IMAGE_URL = "https://media.discordapp.net/attachments/1441453165940707428/1451649452702957598/designer.png?ex=6946f167&is=69459fe7&hm=f6af8bfb2a9f9c1140f8e39b635fb3e7eaa8ed112c13c4306a07fc2c724e65a7&=&format=webp&quality=lossless&width=2940&height=1654"
EDUCATORS_IMAGE_URL = "https://media.discordapp.net/attachments/1441453165940707428/1451649472441352344/educator.png?ex=6946f16c&is=69459fec&hm=0b49231950d69dbc1325c6f2ad934390c803a8edd8e0c55298dc0b3632eeab1a&=&format=webp&quality=lossless&width=2940&height=1654"
TRADERS_IMAGE_URL = "https://media.discordapp.net/attachments/1441453165940707428/1451649482033860608/trader.png?ex=6946f16e&is=69459fee&hm=ace9488b441325134bfd150ba5156316d924e5bf48806daad90ee801342379b8&=&format=webp&quality=lossless&width=2940&height=1654"
TRENDMAKERS_IMAGE_URL = "https://media.discordapp.net/attachments/1441453165940707428/1451649520462205212/trendmaker.png?ex=6946f178&is=69459ff8&hm=1100e2a4b9e567c1324402e24b4356494b4fa331bb2a897dce60138b47a7c975&=&format=webp&quality=lossless&width=2940&height=1654"
CONTENT_LANE_URL = "https://media.discordapp.net/attachments/1441453165940707428/1455250481575100484/content_lanes_2.png?ex=69540b20&is=6952b9a0&hm=1dcf3112c034916105c04910af688e7df1a0fb218a333b2b3fd5e370e2d27e84&=&format=webp&quality=lossless&width=2838&height=1596"

# =============================================================
# footers (microcopy, not slogans)
# - short
# - specific
# - non-cringe
# - no emojis
# =============================================================

FOOTERS: Tuple[str, ...] = (
    "little steps. real progress",
)

def footer() -> str:
    i = int(datetime.utcnow().timestamp() // 3600) % len(FOOTERS)
    return FOOTERS[i]

# =============================================================
# text helpers
# =============================================================

def _set_footer(embed: discord.Embed) -> None:
    embed.set_footer(text=footer())

def soft(text: str) -> str:
    return f"*{text}*"

def bullets(lines: List[str]) -> str:
    return "\n".join(f"• {x}" for x in lines)

def steps(lines: List[str]) -> str:
    return "\n".join(f"{i+1}) {x}" for i, x in enumerate(lines))

def path_text(key: str, with_mentions: bool = False) -> str:
    if key == "traders":
        return (
            "<@&1449055127049605312> > <@&1449055171685515354> > <@&1449055325020754100>"
            if with_mentions
                else "tide > degen > speculator"
        )
    if key == "content":
        return (
            "<@&1449054897486954506> > <@&1449054975107010673> > <@&1449055051829084353>"
            if with_mentions
            else "drip > frame > orator"
        )
    if key == "designers":
        return (
            f"<@&1449054607899758726> > <@&1449054761650225244> > <@&1449054806038675569>"
            if with_mentions
            else "ink > sketch > sculptor"
        )
    return "still unfolding"

# =============================================================
# guild config (human + concrete)
# =============================================================

GUILDS_DATA = {
    "traders": {
        "name": "traders",
        "color": LIQUID,
        "role_id": "1447974772662079549",
        "intro": "this is for people who actually think before clicking buy or sell.",
        "what": [
            "share trade ideas with clear entries, stops and targets",
            "come back and explain what happened after the trade",
            "help others avoid chasing random wins",
        ],
        "fit": "you care about being right more than being loud",
        "path_key": "traders",
    },

    "content": {
        "name": "content",
        "color": PINK_SOFT,
        "role_id": "",
        "intro": "you help control how liquid feels the first time someone sees it.",
        "fit": "you can keep posting without burning out",
        "path_key": "content",
        "lanes": [
            "trendmakers: fun, fast and viral",
            "educators: friendly, patient and good at explaining",
        ],
        "sub_guilds": {
            "trendmakers": {
                "name": "trendmakers",
                "color": PINK_SOFT,
                "role_id": "1447974925712363614",
                "intro": "you know how to catch attention without trying too hard.",
                "what": [
                    "post short content like tweets, memes or clips",
                    "turn updates into something people want to share",
                    "spot what spreads fast",
                ],
                "fit": "you have timing and taste",
                "tip": "one post that spreads is better than five nobody sees",
                "path_key": "content",
            },
            "educators": {
                "name": "educators",
                "color": PURPLE_SOFT,
                "role_id": "1449051926665760852",
                "intro": "you enjoy turning 'wait what' into 'ohh okay'.",
                "what": [
                    "write guides people actually save",
                    "create threads that normal people can get",
                    "help people go from guessing to knowing",
                ],
                "fit": "you don't rush explanations",
                "path_key": "content",
            },
        },
    },

    "designers": {
        "name": "designers",
        "color": DESIGN_PINK,
        "role_id": "1447974376438763671",
        "intro": "you care about how things look and it bothers you when they don't.",
        "what": [
            "make visuals people don't scroll past",
            "keep stuff feeling like it comes from the same place",
            "push everything from 'okay' to 'damn, this looks good'",
        ],
        "fit": "you see when something looks off, even if others don't",
        "path_key": "designers",
    },
}

CONTENT_LANE_KEYS = {"trendmakers", "educators"}

def all_guild_role_ids() -> Set[int]:
    ids: Set[int] = set()
    for g in GUILDS_DATA.values():
        rid = (g.get("role_id") or "").strip()
        if rid:
            ids.add(int(rid))
        for sg in (g.get("sub_guilds") or {}).values():
            srid = (sg.get("role_id") or "").strip()
            if srid:
                ids.add(int(srid))
    return ids

GUILD_ROLE_IDS = all_guild_role_ids()

def get_content_lane_role_ids() -> Dict[str, int]:
    out: Dict[str, int] = {}
    for lane_key, lane in (GUILDS_DATA.get("content", {}).get("sub_guilds") or {}).items():
        rid = (lane.get("role_id") or "").strip()
        if rid:
            out[lane_key] = int(rid)
    return out

CONTENT_LANE_ROLE_IDS = get_content_lane_role_ids()

def count_member_guild_roles(member: discord.Member) -> int:
    return sum(1 for r in member.roles if r.id in GUILD_ROLE_IDS)

def current_content_lane(member: discord.Member) -> Optional[str]:
    for lane_key, rid in CONTENT_LANE_ROLE_IDS.items():
        if any(r.id == rid for r in member.roles):
            return lane_key
    return None

# =============================================================
# embeds (copy: sharp, concrete, non-ai)
# =============================================================

def build_main_embed() -> discord.Embed:
    embed = discord.Embed(
        color=LIQUID,
        title="contribute",
        description=(
            "if you want to help liquid, start here.\n"
            "real effort doesn't go unnoticed.\n\n"

            "**quickstart**\n"
            "- pick a guild\n"
            "- ship something useful\n"
            "- save it in your portfolio\n"
            "- repeat\n\n"

            "**a few things**\n"
            "- you can join up to 2 guilds\n"
            "- quality beats quantity\n"
            "- stuck? ask, people will help"
        ),
    )

    embed.set_image(url=HERO_IMAGE_URL)
    _set_footer(embed)
    return embed

def build_portfolio_embed() -> discord.Embed:
    embed = discord.Embed(
        color=LIQUID_SOFT,
        title="portfolio",
        description=(
            "this is where your contributions live.\n\n"

            "**what to add**\n"
            "- posts, threads, articles\n"
            "- anything useful you created\n\n"

            "**what to do**\n"
            "- go to [buildwithliquid.xyz/portfolio](https://buildwithliquid.xyz/portfolio)\n"
            "- log in with your discord account\n"
            "- paste links to what you made\n"
            "- update it whenever you do something new\n\n"
            
            "**what happens next**\n"
            "- you submit your portfolio\n"
            "- it's reviewed in a public parliament vote\n"
            "- results are shared after 24 hours"      
        ),
    )

    embed.set_image(url=PORTFOLIO_IMAGE_URL)
    return embed

def build_roles_hub_embed() -> discord.Embed:
    embed = discord.Embed(
        color=GOLD_SOFT,
        title="roles",
        description=(
            "they are a result, not a target.\n\n"

            "**paths**\n"
            "- each guild has a simple ladder\n"
            "- progress is based on your work\n\n"

            "**special roles**\n"
            "- handled by the team. no requests needed\n"
            "- based on reputation"
        ),
    )

    embed.set_image(url=ROLES_IMAGE_URL)
    return embed

def build_paths_embed() -> discord.Embed:
    embed = discord.Embed(
        color=LIQUID,
        title="guild paths",
        description=(
            "you can be part of up to two at the same time.\n\n"

            "**traders**\n"
            f"- {E['tide']} tide\n"
            f"- {E['degen']} degen\n"
            f"- {E['speculator']} speculator\n\n"

            "**content**\n"
            f"- {E['drip']} drip\n"
            f"- {E['frame']} frame\n"
            f"- {E['orator']} orator\n\n"

            "**designers**\n"
            f"- {E['ink']} ink\n"
            f"- {E['sketch']} sketch\n"
            f"- {E['sculptor']} sculptor"
        ),
    )

    embed.set_image(url=GUILD_PATHS_IMAGE_URL)
    return embed

def build_special_roles_embed() -> discord.Embed:
    embed = discord.Embed(
        color=GOLD_SOFT,
        title="special roles",
        description=(
            "recognition is earned.\n\n"

            "**> community roles**\n"
            
            f"{E['bigdrop']} **big drop**\n"
            "boosted the server\n\n"

            f"{E['winner']} **event winner**\n"
            "came out on top in a community challenge\n\n"

            f"{E['parliament']} **parliament**\n"
            "trusted people in key decisions\n\n"

            f"{E['foundingdroplet']} **founding droplet**\n"
            "built when nothing was guaranteed\n\n"

            f"{E['allin']} **all in liquid**\n"
            "final tier. extremely rare\n\n"

            "**> team roles**\n"

            f"{E['staff']} **staff**\n"
            "runs things behind the scenes\n\n"

            f"{E['moderator']} **moderator**\n"
            "protects this place and the people in it\n\n"

            f"{E['lead']} **guild lead**\n"
            "keeps the guild healthy\n\n"
        ),
    )

    embed.set_image(url=SPECIAL_ROLES_IMAGE_URL)
    return embed

def build_guilds_embed() -> discord.Embed:
    embed = discord.Embed(
        color=LIQUID,
        title="choose a guild",
        description=(
            f"you can join up to **{MAX_GUILDS}**. pick where you will actually contribute.\n\n"

            f"{E['traders']} **traders**\n"
            f"- {E['tide']} tide\n"
            f"- {E['degen']} degen\n"
            f"- {E['speculator']} speculator\n"
            "charts, entries and trade outcomes\n\n"

            f"{E['content']} **content**\n"
            f"- {E['drip']} drip\n"
            f"- {E['frame']} frame\n"
            f"- {E['orator']} orator\n"
            "posts, guides and things that spread\n\n"

            f"{E['artists']} **designers**\n"
            f"- {E['ink']} ink\n"
            f"- {E['sketch']} sketch\n"
            f"- {E['sculptor']} sculptor\n"
            "visuals, assets and the details that make it feel finished"
        ),
    )

    embed.set_image(url=CHOOSE_GUILD_IMAGE_URL)
    return embed

def build_content_lane_pick_embed() -> discord.Embed:
    embed = discord.Embed(
        color=PINK_SOFT,
        title="pick a content lane",
        description=(
            f"choose the one you can ship in daily.\n\n"
            f"{E['trendmakers']} **trendmakers**\n"
            "- fast posts\n"
            "- memes and clips\n"
            "- built for reach\n\n"
            f"{E['educators']} **educators**\n"
            "- mini guides\n"
            "- concepts made simple\n"
            "- things that finally make sense"
        ),
    )

    embed.set_image(url=CONTENT_LANE_URL)
    return embed

def build_guild_detail_embed(guild_key: str) -> discord.Embed:
    data = GUILDS_DATA.get(guild_key, {})

    title_map = {
        "traders": f"{E['traders']} traders",
        "content": f"{E['content']} content",
        "designers": f"{E['artists']} designers",
    }

    lines: List[str] = []

    # intro
    intro = str(data.get("intro", "loading...")).lower()
    lines.append(intro)
    lines.append("")

    # what you ship
    what_list = data.get("what", [])
    if what_list:
        lines.append("**what you actually ship**")
        for x in what_list:
            lines.append(f"• {x.lower()}")
        lines.append("")

    # content lanes (content only)
    lanes = data.get("lanes")
    if lanes:
        lines.append("**pick one lane**")
        for x in lanes:
            lines.append(f"• {x.lower()}")
        lines.append("")

    # path
    pk = data.get("path_key")
    if pk:
        lines.append("**how it grows**")
        lines.append(f"{path_text(pk)}")
        lines.append("")

    # fit
    fit = data.get("fit")
    if fit:
        lines.append("**you'll do well here if**")
        lines.append(str(fit).lower())
        lines.append("")

    # guild lead
    if guild_key == "traders":
        lines.append(f"{E['lead']} **guild lead**")
        lines.append("<@285676584545812483>")
    elif guild_key == "designers":
        lines.append(f"{E['lead']} **guild lead**")
        lines.append("<@368402714196967425>")

    embed = discord.Embed(
        color=data.get("color", LIQUID),
        title=title_map.get(guild_key, str(data.get("name", guild_key)).lower()),
        description="\n".join(lines).strip(),
    )
    
    if guild_key == "traders":
        embed.set_image(url=TRADERS_IMAGE_URL)
    elif guild_key == "designers":
        embed.set_image(url=DESIGNERS_IMAGE_URL)

    return embed

def build_subguild_detail_embed(parent_key: str, sub_key: str) -> discord.Embed:
    sub = (GUILDS_DATA.get(parent_key, {}).get("sub_guilds") or {}).get(sub_key, {})

    lines: List[str] = []

    # intro
    intro = str(sub.get("intro", "loading...")).lower()
    lines.append(intro)
    lines.append("")

    # what you ship
    what_list = sub.get("what", [])
    if what_list:
        lines.append("**what you'll spend most time on**")
        for x in what_list:
            lines.append(f"• {x.lower()}")
        lines.append("")

    # progression (inherits content path)
    lines.append("**where this leads**")
    lines.append(path_text("content"))
    lines.append("")

    # fit
    fit = sub.get("fit")
    if fit:
        lines.append("**you'll do well here if**")
        lines.append(str(fit).lower())
        lines.append("")

    # lane lead
    if sub_key == "educators":
        lines.append(f"{E['lead']} **guild lead**")
        lines.append("<@518149539253846021>")
    elif sub_key == "trendmakers":
        lines.append(f"{E['lead']} **guild lead**")
        lines.append("<@768484472660033558>")

    embed = discord.Embed(
        color=sub.get("color", LIQUID),
        title=f"{E[sub_key]} {str(sub.get('name', sub_key)).lower()}",
        description="\n".join(lines).strip(),
    )
    
    if sub_key == "educators":
        embed.set_image(url=EDUCATORS_IMAGE_URL)
    elif sub_key == "trendmakers":
        embed.set_image(url=TRENDMAKERS_IMAGE_URL)

    return embed

# =============================================================
# views (buttons carry "path icons", embeds use guild emblems)
# =============================================================

def guild_button_emoji(guild_key: str) -> discord.PartialEmoji:
    if guild_key == "traders":
        return PE["speculator"]
    if guild_key == "content":
        return PE["orator"]
    if guild_key == "designers":
        return PE["sculptor"]
    return PE["lead"]

def join_button_emoji(guild_key: str, sub_key: Optional[str]) -> discord.PartialEmoji:
    if sub_key == "trendmakers":
        return PE["join"]
    if sub_key == "educators":
        return PE["join"]
    if guild_key == "traders":
        return PE["join"]
    if guild_key == "designers":
        return PE["join"]
    if guild_key == "content":
        return PE["join"]
    return PE["lead"]

class GuildConfirmationView(View):
    def __init__(self, guild_key: str, sub_guild_key: Optional[str] = None):
        super().__init__(timeout=300)
        self.guild_key = guild_key
        self.sub_guild_key = sub_guild_key

        self.add_item(Button(
            style=discord.ButtonStyle.success,
            label="join",
            emoji=join_button_emoji(guild_key, sub_guild_key),
            custom_id=f"guild_confirm:yes:{guild_key}:{sub_guild_key or ''}",
        ))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            custom_id = (interaction.data or {}).get("custom_id", "")
            parts = custom_id.split(":")
            if len(parts) < 3:
                return False

            guild_key = parts[2]
            sub_key = parts[3] if len(parts) > 3 and parts[3] else None

            guild = interaction.guild
            if not guild:
                await interaction.response.send_message("this only works inside the server.", ephemeral=True)
                return False

            if sub_key:
                guild_data = (GUILDS_DATA.get(guild_key, {}).get("sub_guilds") or {}).get(sub_key, {})
                guild_name = str(guild_data.get("name", sub_key)).lower()
            else:
                guild_data = GUILDS_DATA.get(guild_key, {})
                guild_name = str(guild_data.get("name", guild_key)).lower()

            role_id = (guild_data.get("role_id") or "").strip()

            member = interaction.user
            if not isinstance(member, discord.Member):
                member = guild.get_member(interaction.user.id)

            if not member:
                await interaction.response.send_message("couldn't find you. try again.", ephemeral=True)
                return True

            # lane exclusivity
            if sub_key in CONTENT_LANE_KEYS:
                existing_lane = current_content_lane(member)
                if existing_lane and existing_lane != sub_key:
                    await interaction.response.send_message(
                        "you already picked a content lane.\n\n"
                        "reach out to the guild lead if you want to switch.",
                        ephemeral=True,
                    )
                    return True

            if not role_id:
                await interaction.response.send_message(
                    f"got it. you're in for **{guild_name}**.\n"
                    "role setup is still in progress.",
                    ephemeral=True,
                )
                return True

            role = guild.get_role(int(role_id))
            if not role:
                await interaction.response.send_message(
                    f"something's missing for **{guild_name}**.\n\n"
                    "ping a staff member and we'll fix it.",
                )
                return True

            if role in member.roles:
                await interaction.response.send_message(f"you're already part of **{guild_name}**.", ephemeral=True)
                return True

            if count_member_guild_roles(member) >= MAX_GUILDS:
                await interaction.response.send_message(
                    f"you've hit the limit of **{MAX_GUILDS}** guilds.\n\n"
                    "ask a guild lead to remove one if you want to switch.",
                    ephemeral=True,
                )
                return True

            await member.add_roles(role, reason=f"joined {guild_name} via contribute")
            await interaction.response.send_message(
                f"you're in. **{role.name.lower()}** unlocked.\n\n"
                f"drop a hello in the guild chat whenever you want.",
                ephemeral=True,
            )
            return True

        except Exception as e:
            logger.error(f"guild_confirm_error: {e}", exc_info=True)
            try:
                await interaction.response.send_message("tiny hiccup. try again.", ephemeral=True)
            except Exception:
                pass
            return False

class SubGuildSelectView(View):
    def __init__(self, parent_key: str):
        super().__init__(timeout=300)
        self.parent_key = parent_key

        self.add_item(SubGuildButton(parent_key, "trendmakers"))
        self.add_item(SubGuildButton(parent_key, "educators"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        custom_id = (interaction.data or {}).get("custom_id", "")
        if not custom_id.startswith("sub_guild:"):
            return False

        _, parent_key, sub_key = custom_id.split(":")

        await interaction.response.edit_message(
            embed=build_subguild_detail_embed(parent_key, sub_key),
            view=GuildConfirmationView(parent_key, sub_key),
        )
        return True


class SubGuildButton(Button):
    def __init__(self, parent_key: str, sub_key: str):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label=sub_key,
            emoji=PE[sub_key],
            custom_id=f"sub_guild:{parent_key}:{sub_key}",
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            custom_id = (interaction.data or {}).get("custom_id", "")
            if not custom_id.startswith("sub_guild:"):
                return False

            parts = custom_id.split(":")
            if len(parts) < 3:
                return False

            parent_key = parts[1]
            sub_key = parts[2]
            await interaction.response.edit_message(
                embed=build_subguild_detail_embed(parent_key, sub_key),
                view=GuildConfirmationView(parent_key, sub_key),
            )
            return True

        except Exception as e:
            logger.error(f"sub_guild_select_error: {e}", exc_info=True)
            return False

class GuildSelectView(View):
    def __init__(self):
        super().__init__(timeout=None)

        for key in ["traders", "content", "designers"]:
            data = GUILDS_DATA.get(key, {})
            if not data:
                continue
            self.add_item(Button(
                style=discord.ButtonStyle.primary,
                label=str(data.get("name", key)).lower(),
                emoji=guild_button_emoji(key),
                custom_id=f"guild_select:{key}",
            ))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            custom_id = (interaction.data or {}).get("custom_id", "")
            if not custom_id.startswith("guild_select:"):
                return False

            guild_key = custom_id.split(":")[1]
            guild_data = GUILDS_DATA.get(guild_key, {})

            if not guild_data:
                await interaction.response.send_message("guild not found.", ephemeral=True)
                return False

            if guild_data.get("sub_guilds"):
                await interaction.response.edit_message(
                    embed=build_content_lane_pick_embed(),
                    view=SubGuildSelectView(guild_key),
                )
                return True

            await interaction.response.edit_message(
                embed=build_guild_detail_embed(guild_key),
                view=GuildConfirmationView(guild_key),
            )
            return True

        except Exception as e:
            logger.error(f"guild_select_error: {e}", exc_info=True)
            try:
                await interaction.response.send_message("something broke. try again.", ephemeral=True)
            except Exception:
                pass
            return False

class RolesSubView(View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(Button(
            style=discord.ButtonStyle.primary,
            label="paths",
            emoji=PE["automata"],
            custom_id="contribute_roles:paths",
        ))
        self.add_item(Button(
            style=discord.ButtonStyle.secondary,
            label="special",
            emoji=PE["allin"],
            custom_id="contribute_roles:special",
        ))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            custom_id = (interaction.data or {}).get("custom_id", "")
            if custom_id == "contribute_roles:paths":
                await interaction.response.send_message(embed=build_paths_embed(), ephemeral=True)
                return True

            if custom_id == "contribute_roles:special":
                await interaction.response.send_message(embed=build_special_roles_embed(), ephemeral=True)
                return True

            return False

        except Exception as e:
            logger.error(f"roles_sub_error: {e}", exc_info=True)
            return False

class ContributeView(View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(Button(
            style=discord.ButtonStyle.primary,
            label="portfolio",
            emoji=PE["portfolio"],
            custom_id="contribute:portfolio",
        ))

        self.add_item(Button(
            style=discord.ButtonStyle.secondary,
            label="roles",
            emoji=PE["winner"],
            custom_id="contribute:roles",
        ))

        self.add_item(Button(
            style=discord.ButtonStyle.success,
            label="guilds",
            emoji=PE["lead"],
            custom_id="contribute:guilds",
        ))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            custom_id = (interaction.data or {}).get("custom_id", "")
            section = custom_id.split(":")[1] if ":" in custom_id else ""

            if section == "portfolio":
                await interaction.response.send_message(embed=build_portfolio_embed(), ephemeral=True)
                return True

            if section == "roles":
                await interaction.response.send_message(
                    embed=build_roles_hub_embed(),
                    view=RolesSubView(),
                    ephemeral=True,
                )
                return True

            if section == "guilds":
                await interaction.response.send_message(
                    embed=build_guilds_embed(),
                    view=GuildSelectView(),
                    ephemeral=True,
                )
                return True

            return False

        except Exception as e:
            logger.error(f"contribute_button_error: {e}", exc_info=True)
            try:
                await interaction.response.send_message("something broke. try again.", ephemeral=True)
            except Exception:
                pass
            return False

# =============================================================
# command handler
# =============================================================

class ContributeCommand:
    """
    !contribute command handler
    """

    def __init__(self):
        self.enabled = True
        self.cooldown_seconds = 60
        self.last_use: Dict[int, float] = {}

    def can_use_command(self, member: discord.Member) -> bool:
        return member.guild_permissions.administrator or member.guild_permissions.manage_guild

    def check_cooldown(self, channel_id: int) -> bool:
        now = datetime.utcnow().timestamp()
        last_time = self.last_use.get(channel_id, 0.0)
        if now - last_time < self.cooldown_seconds:
            return False
        self.last_use[channel_id] = now
        return True

    async def handle_command(self, message: discord.Message) -> bool:
        try:
            if not self.enabled:
                return False
            if not message.content.strip().startswith("!contribute"):
                return False
            if not self.can_use_command(message.author):
                return False
            if not self.check_cooldown(message.channel.id):
                return False

            await message.channel.send(embed=build_main_embed(), view=ContributeView())
            logger.info(f"contribute_command | user=@{message.author.name} | channel={message.channel.id}")
            return True

        except Exception as e:
            logger.error(f"contribute_command_error: {e}", exc_info=True)
