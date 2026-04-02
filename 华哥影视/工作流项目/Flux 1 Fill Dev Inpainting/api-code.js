npm install node-fetch@2 --save

const workflow_id = "VYTkA69tX3-VQAHZNJ5sk"

// Workflow JSON in API Format
const prompt = {"3":{"_meta":{"title":"KSampler"},"inputs":{"cfg":1,"seed":798468516341541,"model":["39",0],"steps":20,"denoise":1,"negative":["38",1],"positive":["38",0],"scheduler":"normal","latent_image":["38",2],"sampler_name":"euler"},"class_type":"KSampler"},"7":{"_meta":{"title":"CLIP Text Encode (Negative Prompt)"},"inputs":{"clip":["34",0],"text":""},"class_type":"CLIPTextEncode"},"8":{"_meta":{"title":"VAE Decode"},"inputs":{"vae":["32",0],"samples":["3",0]},"class_type":"VAEDecode"},"9":{"_meta":{"title":"Save Image"},"inputs":{"images":["8",0],"filename_prefix":"ComfyUI"},"class_type":"SaveImage"},"17":{"_meta":{"title":"Load Image"},"inputs":{"image":"yosemite_inpaint_example.png","upload":"image"},"class_type":"LoadImage"},"23":{"_meta":{"title":"CLIP Text Encode (Positive Prompt)"},"inputs":{"clip":["34",0],"text":"anime girl with massive fennec ears blonde hair blue eyes wearing a pink shirt"},"class_type":"CLIPTextEncode"},"26":{"_meta":{"title":"FluxGuidance"},"inputs":{"guidance":30,"conditioning":["23",0]},"class_type":"FluxGuidance"},"31":{"_meta":{"title":"Load Diffusion Model"},"inputs":{"unet_name":"flux1-fill-dev.safetensors","weight_dtype":"default"},"class_type":"UNETLoader"},"32":{"_meta":{"title":"Load VAE"},"inputs":{"vae_name":"flux1-ae.safetensors"},"class_type":"VAELoader"},"34":{"_meta":{"title":"DualCLIPLoader"},"inputs":{"type":"flux","device":"default","clip_name1":"clip_l.safetensors","clip_name2":"t5xxl_fp16.safetensors"},"class_type":"DualCLIPLoader"},"38":{"_meta":{"title":"InpaintModelConditioning"},"inputs":{"vae":["32",0],"mask":["17",1],"pixels":["17",0],"negative":["7",0],"positive":["26",0],"noise_mask":false},"class_type":"InpaintModelConditioning"},"39":{"_meta":{"title":"Differential Diffusion"},"inputs":{"model":["31",0]},"class_type":"DifferentialDiffusion"}};

// Input files
const files = {
    "/input/yosemite_inpaint_example.png": "https://comfy.icu/api/v1/view/workflows/VYTkA69tX3-VQAHZNJ5sk/input/yosemite_inpaint_example.png"
};

const fetch = require('node-fetch');

async function runWorkflow(body){
    const url = "https://comfy.icu/api/v1/workflows/"+body.workflow_id+"/runs"
    const resp = await fetch(url, {
      "headers": {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": "Bearer " + process.env.COMFYICU_API_KEY
      },
      "body": JSON.stringify(body),
      "method": "POST"
    });

    return await resp.json()
}

async function main() {
    const run = await runWorkflow({workflow_id, prompt, files})
    console.log(run)
}

main()

export COMFYICU_API_KEY="XXX"
node index.js