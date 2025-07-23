from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `history` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `session_id` VARCHAR(36) NOT NULL UNIQUE,
    `conversation` JSON NOT NULL,
    `summary` LONGTEXT,
    `start_time` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `end_time` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='会话历史记录模型 - 存储整个会话的对话历史';
CREATE TABLE IF NOT EXISTS `language_stats` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `language` VARCHAR(10) NOT NULL,
    `stats` INT NOT NULL  DEFAULT 0,
    `last_updated` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='全局语言使用统计模型';
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
