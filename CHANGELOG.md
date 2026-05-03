# Changelog

## v3.2.1 (2026-05-03)

### Added
- AI Bot player (`/bot加入` / `/bot退出`) for 衔字飞花令 and 纵横飞花令
- Bot auto-search database for best matching poems on each turn
- Bot think delay (2-4s) to simulate human player
- Snake poetry game mode (`/蛇形飞花令`)
- `/安装数据库` command with multi-source probe and progress feedback
- Gitee 4-part download as primary source for domestic users
- GitHub mirror fallback (gh.llkk.cc, ghproxy.net, gh.ddlc.top)
- Stream download to disk (prevents memory explosion on small servers)
- Multi-save management (`/恢复游戏 [序号]`, `/删除存档 [序号]`)
- Timeout monitor with auto-skip for inactive players
- Exact/fuzzy dual-mode sentence search in `/查询诗句`
- Author-filtered title search in `/查询诗词 [标题] [作者]`
- Help menu system (`/飞花令帮助`)
- In-game operations: `退出`, `跳过`, `催更`
- FTS5 full-text search index for faster queries
- Multi-version poem support (version field in database)
- Configurable timeout settings per game mode

### Changed
- Database rebuilt from merged poetry-dataset (1,197,883 poems)
- Database installation moved from auto-download to manual command
- Download sources ranked by probe speed before selection
- `.gitattributes` added to prevent encoding corruption on Windows Git
- metadata.yaml uses LF line endings to avoid garbled characters

### Fixed
- Cross-word bot GRID_SIZE attribute error
- Snake bot infinite loop causing game freeze
- In-memory bytearray OOM on small servers
- Chinese quotation marks conflicting with f-string delimiters
- metadata.yaml encoding corruption on Git CRLF conversion
- Overlapping proposals to same target in autumn_blaze plugin

### Changed
- Database sources: chinese-poetry + Werneror/Poetry + poetic-mao
- Traditional Chinese auto-converted to Simplified (OpenCC)
- poetry_data.db replaced with poetry_data.zip (smaller download)

---

## v2.1.5 (2026-03-02)

### Added
- Initial release
- 衔字飞花令 and 纵横飞花令 game modes
- Basic poem search (`/查询诗句`, `/查询诗词`)
- GitHub Release database download
