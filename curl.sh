curl -X POST 'http://localhost:8000/videos' \
--header 'Content-Type: application/json' \
--data '{
    "input_video_path": "video/subway.mp4",
    "crop_alignment": "center",
    "dialogues": [
      [
        {
          "character": "nerd",
          "phrase": "Cara, o que é essa Pindaiba Tech?"
        },
        {
          "character": "careca",
          "phrase": "É uma startup de IA que cria vídeos automáticos!"
        },
        {
          "character": "nerd",
          "phrase": "Sério? Tipo deepfake?"
        },
        {
          "character": "careca",
          "phrase": "Não, cara! Eles fazem conteúdo educativo com personagens virtuais!"
        },
        {
          "character": "nerd",
          "phrase": "Massa! Futuro chegou mesmo!"
        }
      ]
    ],
    "characters": {
        "nerd": {
            "voice_id": "2BJW5coyhAzSr8STdHbE",
            "image_file": "images/nerd.png",
            "position": "bottom_right",
            "scale": 0.5,
            "margin": 0,
            "primary_color": [
                255,
                255,
                255
            ],
            "secondary_color": [
                200,
                200,
                200,
                128
            ]
        },
        "careca": {
            "voice_id": "tTZ0TVc9Q1bbWngiduLK",
            "image_file": "images/father.png",
            "position": "bottom_left",
            "scale": 0.6,
            "margin": 0,
            "primary_color": [
                255,
                255,
                0
            ],
            "secondary_color": [
                200,
                200,
                100,
                128
            ]
        }
    },
    "watermark": true,
    "watermark_text": "pindaiba.vercel.app"
}'
