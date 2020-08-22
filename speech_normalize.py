import os

def clean_wav_filename(wav_dir):
    for wav in os.listdir(wav_dir):
        if wav.endswith(".wav"):
            basename = os.path.basename(wav)
            name, ext = os.path.splitext(basename)
            new_name = '%04d.wav' % (int(name.split('-')[1]))              
            os.rename('%s/%s' % (wav_dir, basename), '%s/%s' % (wav_dir, new_name))

if __name__ == '__main__':
    clean_wav_filename('work/speech/current/wav')
