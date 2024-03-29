# -*- coding: utf-8 -*-
# ***********************************************************************
# ******************  CANADIAN ASTRONOMY DATA CENTRE  *******************
# *************  CENTRE CANADIEN DE DONNÉES ASTRONOMIQUES  **************
#
#  (c) 2020.                            (c) 2020.
#  Government of Canada                 Gouvernement du Canada
#  National Research Council            Conseil national de recherches
#  Ottawa, Canada, K1A 0R6              Ottawa, Canada, K1A 0R6
#  All rights reserved                  Tous droits réservés
#
#  NRC disclaims any warranties,        Le CNRC dénie toute garantie
#  expressed, implied, or               énoncée, implicite ou légale,
#  statutory, of any kind with          de quelque nature que ce
#  respect to the software,             soit, concernant le logiciel,
#  including without limitation         y compris sans restriction
#  any warranty of merchantability      toute garantie de valeur
#  or fitness for a particular          marchande ou de pertinence
#  purpose. NRC shall not be            pour un usage particulier.
#  liable in any event for any          Le CNRC ne pourra en aucun cas
#  damages, whether direct or           être tenu responsable de tout
#  indirect, special or general,        dommage, direct ou indirect,
#  consequential or incidental,         particulier ou général,
#  arising from the use of the          accessoire ou fortuit, résultant
#  software.  Neither the name          de l'utilisation du logiciel. Ni
#  of the National Research             le nom du Conseil National de
#  Council of Canada nor the            Recherches du Canada ni les noms
#  names of its contributors may        de ses  participants ne peuvent
#  be used to endorse or promote        être utilisés pour approuver ou
#  products derived from this           promouvoir les produits dérivés
#  software without specific prior      de ce logiciel sans autorisation
#  written permission.                  préalable et particulière
#                                       par écrit.
#
#  This file is part of the             Ce fichier fait partie du projet
#  OpenCADC project.                    OpenCADC.
#
#  OpenCADC is free software:           OpenCADC est un logiciel libre ;
#  you can redistribute it and/or       vous pouvez le redistribuer ou le
#  modify it under the terms of         modifier suivant les termes de
#  the GNU Affero General Public        la “GNU Affero General Public
#  License as published by the          License” telle que publiée
#  Free Software Foundation,            par la Free Software Foundation
#  either version 3 of the              : soit la version 3 de cette
#  License, or (at your option)         licence, soit (à votre gré)
#  any later version.                   toute version ultérieure.
#
#  OpenCADC is distributed in the       OpenCADC est distribué
#  hope that it will be useful,         dans l’espoir qu’il vous
#  but WITHOUT ANY WARRANTY;            sera utile, mais SANS AUCUNE
#  without even the implied             GARANTIE : sans même la garantie
#  warranty of MERCHANTABILITY          implicite de COMMERCIALISABILITÉ
#  or FITNESS FOR A PARTICULAR          ni d’ADÉQUATION À UN OBJECTIF
#  PURPOSE.  See the GNU Affero         PARTICULIER. Consultez la Licence
#  General Public License for           Générale Publique GNU Affero
#  more details.                        pour plus de détails.
#
#  You should have received             Vous devriez avoir reçu une
#  a copy of the GNU Affero             copie de la Licence Générale
#  General Public License along         Publique GNU Affero avec
#  with OpenCADC.  If not, see          OpenCADC ; si ce n’est
#  <http://www.gnu.org/licenses/>.      pas le cas, consultez :
#                                       <http://www.gnu.org/licenses/>.
#
#  $Revision: 4 $
#
# ***********************************************************************
#

import re

import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits
from astropy.visualization import MinMaxInterval, ZScaleInterval

from caom2 import ReleaseType
from caom2pipe import manage_composable as mc


class GemProcPreview(mc.PreviewVisitor):
    def __init__(self, observation, **kwargs):
        super(GemProcPreview, self).__init__(
            'GEMINICADC', ReleaseType.DATA, **kwargs
        )
        self._observation = observation

    def generate_plots(self, obs_id):
        self._logger.debug(f'Begin generate_plots for {obs_id}')
        count = 0
        # NC - algorithm
        # NC - review - 07-08-20
        hdus = fits.open(self._science_fqn)
        obs_type = hdus[0].header.get('OBSTYPE').upper()
        interval = ZScaleInterval()
        if (
            self._observation.target is not None
            and self._observation.target.moving
        ) and obs_type != 'DARK':
            interval = MinMaxInterval()
        if 'OBJECT' in obs_type:
            white_light_data = interval(
                np.flipud(np.median(hdus['SCI'].data, axis=0))
            )
        elif (
            'FLAT' in obs_type
            or 'ARC' in obs_type
            or 'RONCHI' in obs_type
            or 'DARK' in obs_type
        ):
            # Stitch together the 29 'SCI' extensions into one array and save.
            hdul = [x for x in hdus if x.name == 'SCI']
            hdul.sort(
                key=lambda x: int(
                    re.split(r"[\[\]\:\,']+", x.header['NSCUTSEC'])[3]
                )
            )
            temp = np.concatenate([x.data for x in hdul])
            white_light_data = interval(temp)
        elif 'SHIFT' in obs_type:
            temp = np.flipud(hdus['SCI'].data)
            white_light_data = interval(temp)
        else:
            return count

        plt.figure(figsize=(10.24, 10.24), dpi=100)
        plt.grid(False)
        plt.axis('off')
        plt.imshow(white_light_data, cmap='inferno')
        plt.savefig(self._preview_fqn, format='jpg')
        count = self._save_figure()
        self._logger.info(f'End generate_plots for {obs_id}.')
        return count


def visit(observation, **kwargs):
    return GemProcPreview(observation, **kwargs).visit(observation)
