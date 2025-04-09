import { McpError, ErrorCode } from '@modelcontextprotocol/sdk/types.js';
import fs from 'fs/promises';
import path from 'path';
export class BackupManager {
    constructor(backupDir, logger) {
        this.backupDir = backupDir;
        this.logger = logger;
    }
    async ensureBackupDir() {
        try {
            await fs.mkdir(this.backupDir, { recursive: true });
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            throw new McpError(ErrorCode.InternalError, `Failed to create backup directory: ${message}`);
        }
    }
    getBackupPath(collection) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        return path.join(this.backupDir, `${collection}_${timestamp}.json`);
    }
    async backup(client, collection) {
        this.logger.info(`Starting backup for collection: ${collection}`);
        try {
            await this.ensureBackupDir();
            const backupPath = this.getBackupPath(collection);
            // Get collection info
            const collectionInfo = await client.getCollection(collection);
            // Get all points
            const points = await client.scroll(collection, {
                with_payload: true,
                with_vector: true,
                limit: 10000 // Adjust based on collection size
            });
            const backup = {
                timestamp: new Date().toISOString(),
                collection: collection,
                info: collectionInfo,
                points: points.points
            };
            await fs.writeFile(backupPath, JSON.stringify(backup, null, 2));
            this.logger.info(`Backup completed: ${backupPath}`);
            // Cleanup old backups
            await this.cleanupOldBackups(collection);
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            this.logger.error('Backup failed:', { error });
            throw new McpError(ErrorCode.InternalError, `Failed to create backup: ${message}`);
        }
    }
    async restore(client, collection) {
        this.logger.info(`Starting restore for collection: ${collection}`);
        try {
            // Get latest backup
            const backup = await this.getLatestBackup(collection);
            if (!backup) {
                throw new Error('No backup found');
            }
            // Recreate collection with original configuration
            await client.createCollection(collection, backup.info.config);
            // Restore points in batches
            const batchSize = 100;
            for (let i = 0; i < backup.points.length; i += batchSize) {
                const batch = backup.points.slice(i, i + batchSize);
                await client.upsert(collection, {
                    wait: true,
                    points: batch
                });
            }
            this.logger.info('Restore completed successfully');
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            this.logger.error('Restore failed:', { error });
            throw new McpError(ErrorCode.InternalError, `Failed to restore from backup: ${message}`);
        }
    }
    async getLatestBackup(collection) {
        try {
            const files = await fs.readdir(this.backupDir);
            const backupFiles = files.filter(file => file.startsWith(collection) && file.endsWith('.json'));
            if (backupFiles.length === 0) {
                return null;
            }
            // Sort by timestamp (newest first)
            backupFiles.sort().reverse();
            const latestBackupPath = path.join(this.backupDir, backupFiles[0]);
            const backupContent = await fs.readFile(latestBackupPath, 'utf8');
            return JSON.parse(backupContent);
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            throw new McpError(ErrorCode.InternalError, `Failed to get latest backup: ${message}`);
        }
    }
    async cleanupOldBackups(collection) {
        try {
            const files = await fs.readdir(this.backupDir);
            const backupFiles = files.filter(file => file.startsWith(collection) && file.endsWith('.json'));
            // Keep only the last 5 backups
            const maxBackups = 5;
            if (backupFiles.length > maxBackups) {
                // Sort by timestamp (oldest first)
                backupFiles.sort();
                // Remove older backups
                const filesToRemove = backupFiles.slice(0, backupFiles.length - maxBackups);
                for (const file of filesToRemove) {
                    await fs.unlink(path.join(this.backupDir, file));
                    this.logger.debug(`Removed old backup: ${file}`, { file });
                }
            }
        }
        catch (error) {
            this.logger.error('Failed to cleanup old backups:', { error });
            // Don't throw error for cleanup failures
        }
    }
}
