curl -X POST 'http://localhost:8000/videos' \
--header 'Content-Type: application/json' \
--data '{
    "input_video_path": "video/coding-asmr.mp4",
    "dialogues": [
      [
        {
          "character": "stewie",
          "phrase": "Bom dia, eu sou o Stewie Griffin, vamos ver o que acontece"
        },
        {
          "character": "peter",
          "phrase": "Bom dia, eu sou o Peter Griffin, vamos ver o que acontece"
        }
      ]
    ],
    "characters": {
        "peter": {
            "voice_id": "MnLB3WqmrDuaBBzpe8tM",
            "image_file": "images/peter.png",
            "position": "bottom_left",
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
        "stewie": {
            "voice_id": "peBmLMo9G6E3bSbuVXeV",
            "image_file": "images/stewie.png",
            "position": "bottom_right",
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
    }
}'
