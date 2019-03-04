// @flow
import React from 'react';
/* eslint-disable import/no-extraneous-dependencies */
import initStoryshots from '@storybook/addon-storyshots';
import { configure, shallow } from 'enzyme';
import Adapter from 'enzyme-adapter-react-16.3';
/* eslint-enable */

import Tags from './tags';
import type { Props } from './tags';

initStoryshots({
  storyKindRegex: /^Tags\|TagContainer$/
});

configure({ adapter: new Adapter() });

describe('<Tags /> - with shallow', () => {
  let wrapper;
  let tagsProps: Props;

  beforeEach(() => {
    tagsProps = {
      tagsList: [{ id: 'Habitat et SDF', text: 'Habitat et SDF' }, { id: 'Facilitation', text: 'Facilitation' }]
    };
    wrapper = shallow(<Tags {...tagsProps} />);
  });

  it('should render a ReactTags component', () => {
    expect(wrapper.find('DragDropContext(ReactTags)')).toHaveLength(1);
  });
});