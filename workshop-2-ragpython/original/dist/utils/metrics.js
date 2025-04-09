export class MetricsCollector {
    constructor() {
        this.operations = new Map();
        this.errors = new Map();
        this.timings = new Map();
    }
    startOperation(name) {
        this.timings.set(name, Date.now());
        this.incrementCounter(this.operations, name);
    }
    endOperation(name) {
        const startTime = this.timings.get(name);
        if (startTime) {
            const duration = Date.now() - startTime;
            console.log(`Operation ${name} completed in ${duration}ms`);
            this.timings.delete(name);
        }
    }
    recordError(operation) {
        this.incrementCounter(this.errors, operation);
    }
    getStats() {
        return {
            operations: Object.fromEntries(this.operations),
            errors: Object.fromEntries(this.errors),
            activeOperations: Array.from(this.timings.keys())
        };
    }
    incrementCounter(counter, key) {
        const current = counter.get(key) || 0;
        counter.set(key, current + 1);
    }
}
