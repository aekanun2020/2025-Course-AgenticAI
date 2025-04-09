export var LogLevel;
(function (LogLevel) {
    LogLevel["DEBUG"] = "DEBUG";
    LogLevel["INFO"] = "INFO";
    LogLevel["WARN"] = "WARN";
    LogLevel["ERROR"] = "ERROR";
})(LogLevel || (LogLevel = {}));
export class Logger {
    constructor(component) {
        this.component = component;
    }
    debug(message, ...args) {
        this.log(LogLevel.DEBUG, message, ...args);
    }
    info(message, ...args) {
        this.log(LogLevel.INFO, message, ...args);
    }
    warn(message, ...args) {
        this.log(LogLevel.WARN, message, ...args);
    }
    error(message, ...args) {
        this.log(LogLevel.ERROR, message, ...args);
    }
    log(level, message, ...args) {
        const timestamp = new Date().toISOString();
        const logMessage = `${timestamp} [${level}] ${this.component}: ${message}`;
        // Add any additional arguments
        if (args.length > 0) {
            console.log(logMessage, ...args);
        }
        else {
            console.log(logMessage);
        }
    }
}
