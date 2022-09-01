import tempfile
from typing import Iterator

import torch
import torch.backends.cudnn
from cog import BasePredictor, Input, Path
from min_dalle import MinDalle

torch.backends.cudnn.deterministic = False


class ReplicatePredictor(BasePredictor):
    def setup(self):
        self.model = MinDalle(dtype=torch.float16, is_mega=False, is_reusable=True)

    def predict(
        self,
        Prompt: str = Input(
            description='For long prompts, only the first 64 tokens will be used to generate the image.',
            default='Dali painting of WALL·E'
        ),
        intermediate_outputs: bool = Input(
            description='Whether to show intermediate outputs while running.  This adds less than a second to the run time.',
            default=False
        ),
        grid_size: int = Input(
            description='Size of the image grid.  4x4 takes about 15 seconds, 8x8 takes about 35 seconds',
            ge=1,
            le=8,
            default=4
        ),
        log2_supercondition_factor: int = Input(
            description='Higher values result in better agreement with the text but a narrower variety of generated images',
            ge=1,
            le=6,
            default=4
        ),
    ) -> Iterator[Path]:
        print("running prediction")
        text = Prompt
        try: 
            seed = -1
            log2_mid_count = 3 if intermediate_outputs else 0
            image_stream = self.model.generate_image_stream(
                text,
                seed,
                grid_size=grid_size,
                log2_mid_count=log2_mid_count,
                log2_supercondition_factor=log2_supercondition_factor,
                is_verbose=True
            )

            iter = 0
            path = Path(tempfile.mkdtemp())
            for image in image_stream:
                iter += 1
                image_path = path / 'min-dalle-iter-{}.jpg'.format(iter)
                image.save(str(image_path))
                yield image_path
        except:
            print("An error occured, deleting model")
            del self.model
            torch.cuda.empty_cache()
            self.setup()
            raise Exception("There was an error, please try again")
