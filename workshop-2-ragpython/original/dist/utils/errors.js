export var AppErrorCode;
(function (AppErrorCode) {
    AppErrorCode["InternalError"] = "INTERNAL_ERROR";
    AppErrorCode["InvalidParams"] = "INVALID_PARAMS";
    AppErrorCode["SecurityError"] = "SECURITY_ERROR";
    AppErrorCode["NetworkError"] = "NETWORK_ERROR";
    AppErrorCode["NotFound"] = "NOT_FOUND";
    AppErrorCode["TooManyRequests"] = "TOO_MANY_REQUESTS";
})(AppErrorCode || (AppErrorCode = {}));
export class ApplicationError extends Error {
    constructor(message, code, context) {
        super(message);
        this.code = code;
        this.context = context;
        this.name = this.constructor.name;
        Error.captureStackTrace(this, this.constructor);
    }
    toJSON() {
        return {
            name: this.name,
            message: this.message,
            code: this.code,
            context: this.context,
            stack: this.stack
        };
    }
}
export class ProcessingError extends ApplicationError {
    constructor(message, context) {
        super(message, AppErrorCode.InternalError, context);
    }
}
export class ValidationError extends ApplicationError {
    constructor(message, context) {
        super(message, AppErrorCode.InvalidParams, context);
    }
}
export class DatabaseError extends ApplicationError {
    constructor(message, context) {
        super(message, AppErrorCode.InternalError, context);
    }
}
export class SecurityError extends ApplicationError {
    constructor(message, context) {
        super(message, AppErrorCode.SecurityError, context);
    }
}
export class NetworkError extends ApplicationError {
    constructor(message, context) {
        super(message, AppErrorCode.NetworkError, context);
    }
}
export class ResourceNotFoundError extends ApplicationError {
    constructor(message, context) {
        super(message, AppErrorCode.NotFound, context);
    }
}
export class RateLimitError extends ApplicationError {
    constructor(message, context) {
        super(message, AppErrorCode.TooManyRequests, context);
    }
}
export function handleError(error) {
    if (error instanceof ApplicationError) {
        return error;
    }
    const errorMessage = error instanceof Error ? error.message : String(error);
    return new ApplicationError(errorMessage, AppErrorCode.InternalError, { originalError: error });
}
