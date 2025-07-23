from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `history` ADD `category` VARCHAR(255);
        ALTER TABLE `history` ADD `title` VARCHAR(255);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `history` DROP COLUMN `category`;
        ALTER TABLE `history` DROP COLUMN `title`;"""
