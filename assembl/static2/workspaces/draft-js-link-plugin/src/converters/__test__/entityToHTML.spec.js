// @flow
import { ContentState } from 'draft-js';
import { constants } from 'assembl-editor-utils';

import entityToHTML from '../entityToHTML';

const { ENTITY_MUTABILITY, ENTITY_TYPES } = constants;

function createEntity(type, mutability, data) {
  let contentState = ContentState.createFromText('');
  contentState = contentState.createEntity(type, mutability, data);
  const entityKey = contentState.getLastCreatedEntityKey();
  return contentState.getEntity(entityKey);
}

describe('entityToHTML function', () => {
  it('should transform entity and original text into a <a> tag', () => {
    const originalText = 'virtual hard drive';
    const entity = createEntity(ENTITY_TYPES.link, ENTITY_MUTABILITY.mutable, {
      target: '_blank',
      title: 'Bluenove',
      url: 'http://www.bluenove.com'
    });
    const expected = '<a href="http://www.bluenove.com" target="_blank" title="Bluenove">virtual hard drive</a>';
    const actual = entityToHTML(entity, originalText);
    expect(actual).toEqual(expected);
  });

  it('should not include target and title in tag if these are not in data', () => {
    const originalText = 'virtual hard drive';
    const entity = createEntity(ENTITY_TYPES.link, ENTITY_MUTABILITY.mutable, {
      url: 'http://www.bluenove.com'
    });
    const expected = '<a href="http://www.bluenove.com">virtual hard drive</a>';
    const actual = entityToHTML(entity, originalText);
    expect(actual).toEqual(expected);
  });
});