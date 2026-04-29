// Logger utility for AI Debug MCP
export var LogLevel;
(function (LogLevel) {
    LogLevel["DEBUG"] = "debug";
    LogLevel["INFO"] = "info";
    LogLevel["WARN"] = "warn";
    LogLevel["ERROR"] = "error";
})(LogLevel || (LogLevel = {}));
const LOG_LEVEL_PRIORITY = {
    [LogLevel.DEBUG]: 0,
    [LogLevel.INFO]: 1,
    [LogLevel.WARN]: 2,
    [LogLevel.ERROR]: 3,
};
class Logger {
    minLevel = LogLevel.INFO;
    setLevel(level) {
        this.minLevel = level;
    }
    shouldLog(level) {
        return LOG_LEVEL_PRIORITY[level] >= LOG_LEVEL_PRIORITY[this.minLevel];
    }
    debug(...args) {
        if (this.shouldLog(LogLevel.DEBUG)) {
            console.debug("[DEBUG]", ...args);
        }
    }
    info(...args) {
        if (this.shouldLog(LogLevel.INFO)) {
            console.info("[INFO]", ...args);
        }
    }
    warn(...args) {
        if (this.shouldLog(LogLevel.WARN)) {
            console.warn("[WARN]", ...args);
        }
    }
    error(...args) {
        if (this.shouldLog(LogLevel.ERROR)) {
            console.error("[ERROR]", ...args);
        }
    }
}
export const logger = new Logger();
