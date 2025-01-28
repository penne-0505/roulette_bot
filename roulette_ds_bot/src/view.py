import discord


class MemberSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(
            placeholder="あみだくじに参加するメンバーを選択してください",
            min_values=1,
            max_values=25,
        )
    
    async def callback(self, interaction):
        
