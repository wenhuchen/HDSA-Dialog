wget --directory-prefix=data/  https://hdsa-dialog.s3-us-west-2.amazonaws.com/delex.json

mkdir -p checkpoints
mkdir -p checkpoints/predictor
mkdir -p checkpoints/generator

wget --directory-prefix=checkpoints/generator/ https://hdsa-dialog.s3-us-west-2.amazonaws.com/BERT_dim128_w_domain
wget --directory-prefix=checkpoints/predictor/ https://hdsa-dialog.s3-us-west-2.amazonaws.com/save_step_15120.zip 
unzip checkpoints/predictor/save_step_15120.zip -d checkpoints/predictor/
