from inferencesh import BaseApp, BaseAppSetup, File, OutputMeta
from pydantic import BaseModel, Field
from typing import Optional
import torch
from diffusers import StableDiffusionXLPipeline, StableDiffusionPipeline
from PIL import Image
import io
import os

class AppSetup(BaseAppSetup):
    """图像生成应用配置"""
    model_id: str = Field(
        default="stabilityai/stable-diffusion-xl-base-1.0",
        description="Hugging Face模型ID"
    )
    use_sdxl: bool = Field(
        default=True,
        description="是否使用SDXL (更快更好)"
    )

class RunInput(BaseModel):
    """图像生成输入"""
    prompt: str = Field(description="图像生成提示词")
    negative_prompt: Optional[str] = Field(
        default=None,
        description="负面提示词（不想出现的内容）"
    )
    width: int = Field(default=1024, description="图像宽度")
    height: int = Field(default=1024, description="图像高度")
    num_inference_steps: int = Field(default=25, description="推理步数")
    guidance_scale: float = Field(default=7.5, description="引导系数")

class RunOutput(BaseModel):
    """图像生成输出"""
    image: File = Field(description="生成的图像文件")
    seed: int = Field(description="使用的随机种子")


class App(BaseApp):

    async def setup(self, config: AppSetup):
        """初始化图像生成模型"""
        print(f"正在加载模型: {config.model_id}")

        if config.use_sdxl:
            # 使用SDXL (更快更好)
            self.pipe = StableDiffusionXLPipeline.from_pretrained(
                config.model_id,
                torch_dtype=torch.float16,
                use_safetensors=True,
                variant="fp16"
            )
        else:
            # 使用SD 1.5
            self.pipe = StableDiffusionPipeline.from_pretrained(
                config.model_id,
                torch_dtype=torch.float16,
                use_safetensors=True,
                variant="fp16"
            )

        # 移动到GPU
        self.pipe = self.pipe.to("cuda")
        self.pipe.enable_model_cpu_offload()

        print("模型加载完成!")

    async def run(self, input_data: RunInput) -> RunOutput:
        """生成图像"""

        # 生成图像
        result = self.pipe(
            prompt=input_data.prompt,
            negative_prompt=input_data.negative_prompt,
            width=input_data.width,
            height=input_data.height,
            num_inference_steps=input_data.num_inference_steps,
            guidance_scale=input_data.guidance_scale
        )

        # 获取图像和种子
        image = result.images[0]
        seed = result.seed

        # 保存到临时文件
        output_path = "/tmp/generated_image.png"
        image.save(output_path)

        return RunOutput(
            image=File(path=output_path),
            seed=seed
        )
