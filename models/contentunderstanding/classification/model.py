#   Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import paddle.fluid as fluid
from paddlerec.core.utils import envs
from paddlerec.core.model import ModelBase


class Model(ModelBase):
    def __init__(self, config):
        ModelBase.__init__(self, config)
        self.dict_dim = 100
        self.max_len = 10
        self.cnn_dim = 32
        self.cnn_filter_size = 128
        self.emb_dim = 8
        self.hid_dim = 128
        self.class_dim = 2
        self.is_sparse = envs.get_global_env("hyper_parameters.is_sparse",
                                             False)

    def input_data(self, is_infer=False, **kwargs):
        data = fluid.data(
            name="input", shape=[None, self.max_len], dtype='int64')
        label = fluid.data(name="label", shape=[None, 1], dtype='int64')
        seq_len = fluid.data(name="seq_len", shape=[None], dtype='int64')
        return [data, label, seq_len]

    def net(self, input, is_infer=False):
        """ network definition """
        data = input[0]
        label = input[1]
        seq_len = input[2]

        # embedding layer
        emb = fluid.embedding(
            input=data,
            size=[self.dict_dim, self.emb_dim],
            is_sparse=self.is_sparse)
        emb = fluid.layers.sequence_unpad(emb, length=seq_len)
        # convolution layer
        conv = fluid.nets.sequence_conv_pool(
            input=emb,
            num_filters=self.cnn_dim,
            filter_size=self.cnn_filter_size,
            act="tanh",
            pool_type="max")

        # full connect layer
        fc_1 = fluid.layers.fc(input=[conv], size=self.hid_dim)
        # softmax layer
        prediction = fluid.layers.fc(input=[fc_1],
                                     size=self.class_dim,
                                     act="softmax")
        cost = fluid.layers.cross_entropy(input=prediction, label=label)
        avg_cost = fluid.layers.mean(x=cost)
        acc = fluid.layers.accuracy(input=prediction, label=label)

        self._cost = avg_cost
        if is_infer:
            self._infer_results["acc"] = acc
        else:
            self._metrics["acc"] = acc
