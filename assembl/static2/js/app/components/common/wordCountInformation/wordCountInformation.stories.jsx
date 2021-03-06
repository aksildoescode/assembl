// @flow
import React from 'react';
/* eslint-disable import/no-extraneous-dependencies */
import { storiesOf } from '@storybook/react';
import { withKnobs, number } from '@storybook/addon-knobs';
/* eslint-enable */

import WordCountInformation from './wordCountInformation';
import type { Props as WordCountInformationProps } from './wordCountInformation';

export const defaultWordCountInformationProps: WordCountInformationProps = {
  wordCount: 50,
  className: ''
};

const playground = {
  wordCount: 120
};

storiesOf('Semantic Analysis|WordCountInformation', module)
  .addDecorator(withKnobs)
  .add('default', () => <WordCountInformation {...defaultWordCountInformationProps} />)
  .add('playground', () => <WordCountInformation wordCount={number('words count', playground.wordCount)} />);