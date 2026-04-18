/**
 * 日志工具
 * 提供分级日志输出（带颜色）
 */

import chalk from 'chalk';

export const logger = {
  info: (msg: string) => console.log(chalk.blue('[INFO]'), msg),
  success: (msg: string) => console.log(chalk.green('[SUCCESS]'), msg),
  warn: (msg: string) => console.log(chalk.yellow('[WARN]'), msg),
  error: (msg: string) => console.log(chalk.red('[ERROR]'), msg),
  stage: (stage: string, msg: string) =>
    console.log(chalk.magenta(`[${stage}]`), msg),
  thinking: (thought: string) =>
    console.log(chalk.gray('思考:'), thought),
  user: (msg: string) =>
    console.log(chalk.cyan('用户:'), msg),
};
