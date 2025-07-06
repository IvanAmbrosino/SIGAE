#!/usr/bin/python3
from ftplib import FTP
import os.path


class ManageFile():
    """Mueve los archivos entre el servicio y la SCC"""

    def __connect(self, host, user, passwd):
        """Connect to host"""
        ftp = FTP(host)
        ftp.set_pasv(0)
        print("Welcome: ",ftp.getwelcome())
        ftp.login(user, passwd)
        return ftp

    def __put_file(self, ftp, path, filename):
        """Envia los rciSched"""
        print(ftp.cwd(path))
        print(ftp.pwd())
        print(filename)
        ftp.storbinary(f'STOR {os.path.basename(filename)}', open(filename,'rb'))
        return

    def __get_file(self, ftp, sched, outpath):
        """Recupera los importSched"""
        with open(f'{outpath}/{sched}', 'wb') as fp:
            ftp.retrbinary(f'RETR {sched}', fp.write)

    def __close_conn(self, ftp):
        """Cierra la conexion al terminar de pasar los archivos."""
        ftp.quit()
        ftp.close()

    def get_sched(self, host, user, passwd, path, outpath, mask):
        """Rutina para recuperar el import sched"""
        ftp = self.__connect(host, user, passwd)
        # Muevo al directorio donde estan los archivo.
        ftp.cwd(path)
        # Obtengo los archivos en el directorio y si los recupero
        file_list = []
        for sched in ftp.nlst(f'*{mask}*'):
            self.__get_file( ftp, sched, outpath)
            file_list.append(sched)
        self.__close_conn(ftp)
        return file_list

    def put_rci_sched(self, host, user, passwd, path, filename):
        """Rutina para enviar el import sched"""
        ftp = self.__connect(host, user, passwd)
        self.__put_file( ftp, path, filename)
        self.__close_conn(ftp)
        
    def __init__(self) -> None:
        pass
